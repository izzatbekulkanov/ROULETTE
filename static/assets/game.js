const { createApp } = Vue;

const app = createApp({
  data() {
    return {
      topicSlug: this.extractTopicSlug(),
      questions: [],
      usedQuestionIds: [],
      outerAngle: 0,
      innerAngle: 0,
      outerRadius: 270,
      innerRadius: 220,
      centerX: 300,
      centerY: 300,
      arrowAngle: Math.PI / 90,
      correctAnswerText: '',
      isSpinning: false,
      isLoading: false
    };
  },
  mounted() {
    this.canvas = document.getElementById('wheel');
    this.ctx = this.canvas.getContext('2d');
    this.startSession();
  },
  methods: {
    extractTopicSlug: function() {
      const match = window.location.pathname.match(/\/topic\/([^\/]+)\/session\//);
      return match ? match[1] : 'default';
    },
    apiFetch: async function(endpoint, options = {}, expectJson = true, retries = 2) {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      try {
        const response = await fetch(`/topic/${this.topicSlug}/${endpoint}`, {
          headers: { 'X-CSRFToken': this.getCsrfToken(), 'Content-Type': 'application/json' },
          signal: controller.signal,
          ...options
        });
        clearTimeout(timeoutId);
        if (!response.ok) {
          if (response.status === 404) {
            throw new Error('Sessiya yoki savollar topilmadi');
          }
          if ((response.status === 429 || response.status >= 500) && retries > 0) {
            await new Promise(resolve => setTimeout(resolve, 1000));
            return this.apiFetch(endpoint, options, expectJson, retries - 1);
          }
          throw new Error(`API xato: ${response.status}`);
        }
        if (!expectJson) return;
        const text = await response.text();
        if (text.startsWith('<!DOCTYPE')) throw new Error('HTML o‘rniga JSON kutilmoqda');
        return JSON.parse(text);
      } catch (error) {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError' && retries > 0) {
          await new Promise(resolve => setTimeout(resolve, 1000));
          return this.apiFetch(endpoint, options, expectJson, retries - 1);
        }
        Swal.fire('Xato', `Server xatosi: ${error.message}`, 'error');
        throw error;
      }
    },
    startSession: async function() {
      await this.apiFetch('session/', {}, false);
      await this.fetchQuestions();
    },
    fetchQuestions: async function() {
      if (this.isLoading) return;
      this.isLoading = true;
      Swal.fire({
        title: 'Savollar yuklanmoqda...',
        allowOutsideClick: false,
        didOpen: () => Swal.showLoading()
      });
      try {
        const data = await this.apiFetch('questions-json/');
        this.questions = (data.questions || []).filter(q => q.selected_answer_id === null).map(q => ({
          ...q,
          answers: this.shuffleArray([...q.answers])
        }));
        this.usedQuestionIds = [];
        Swal.close();
        if (!this.questions.length) {
          Swal.fire('Eslatma', 'Javob berilmagan savollar tugadi.', 'info');
          await this.completeSession();
          return;
        }
        this.drawWheel();
      } catch (error) {
        Swal.close();
        Swal.fire('Xato', 'Savollar yuklanmadi, qayta urinib ko‘ring.', 'error');
      } finally {
        this.isLoading = false;
      }
    },
    submitAnswer: async function() {
      const selectedQuestion = this.getSelectedQuestion();
      if (!selectedQuestion) return;
      const sectorCount = selectedQuestion.answers.length;
      const questionIndex = this.getIndex(this.outerAngle, sectorCount);
      const answerIndex = this.getIndex(this.innerAngle, sectorCount);
      const question = this.questions[questionIndex];
      const answer = question?.answers[answerIndex];

      if (!question || !answer) {
        Swal.fire('Xato', 'Savol yoki javob tanlanmadi.', 'warning');
        return;
      }

      const result = await this.apiFetch('submit-answer/', {
        method: 'POST',
        body: JSON.stringify({ question_id: question.id, answer_id: answer.id })
      });

      Swal.fire({
        icon: result.is_correct ? 'success' : 'error',
        title: result.is_correct ? '✅ To‘g‘ri!' : '❌ Noto‘g‘ri!',
        text: result.explanation
      }).then(() => {
        this.questions.splice(questionIndex, 1);
        this.usedQuestionIds.push(question.id);
        if (this.questions.length === 0) {
          this.completeSession();
        } else if (this.questions.length === 1) {
          this.outerAngle = 0;
          this.drawWheel();
        } else {
          this.spin();
        }
      });
    },
    completeSession: async function() {
      const result = await this.apiFetch('complete/', { method: 'POST' });
      Swal.fire('Sessiya yakunlandi!', 'Barcha savollar tugadi.', 'success').then(() => {
        if (result.redirect_url) window.location.href = result.redirect_url;
      });
    },
    checkAnswer: function() {
      this.submitAnswer();
    },
    getIndex: function(angle, sectorCount) {
      return Math.floor(((-angle % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI) / (2 * Math.PI / sectorCount));
    },
    getSelectedQuestion: function() {
      const sectorCount = this.questions[0]?.answers.length || 8;
      return this.questions[this.getIndex(this.outerAngle, sectorCount)] || null;
    },
    wrapText: function(text, maxWidth) {
      const words = text.split(' ');
      let lines = [];
      let currentLine = words[0];
      for (let i = 1; i < words.length; i++) {
        const testLine = currentLine + ' ' + words[i];
        const metrics = this.ctx.measureText(testLine);
        if (metrics.width > maxWidth) {
          lines.push(currentLine);
          currentLine = words[i];
        } else {
          currentLine = testLine;
        }
      }
      lines.push(currentLine);
      return lines;
    },
    drawWheel: function() {
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
      if (!this.questions.length) {
        this.ctx.fillStyle = '#004d40';
        this.ctx.font = 'bold 24px Roboto';
        this.ctx.textAlign = 'center';
        this.ctx.fillText('Savollar tayyorlanmoqda...', this.centerX, 50);
        return;
      }
      const selectedQuestion = this.getSelectedQuestion();
      const sectorCount = selectedQuestion?.answers.length || 8;

      const gradient = this.ctx.createRadialGradient(
        this.centerX + this.outerRadius * Math.cos(this.arrowAngle),
        this.centerY + this.outerRadius * Math.sin(this.arrowAngle),
        5, this.centerX + this.outerRadius * Math.cos(this.arrowAngle),
        this.centerY + this.outerRadius * Math.sin(this.arrowAngle), 15
      );
      gradient.addColorStop(0, '#4CAF50');
      gradient.addColorStop(1, '#2e7d32');
      this.ctx.fillStyle = gradient;
      this.ctx.beginPath();
      this.ctx.arc(
        this.centerX + this.outerRadius * Math.cos(this.arrowAngle),
        this.centerY + this.outerRadius * Math.sin(this.arrowAngle),
        15, 0, 2 * Math.PI
      );
      this.ctx.fill();

      const outerGradient = this.ctx.createLinearGradient(this.centerX, this.centerY - this.outerRadius, this.centerX, this.centerY + this.outerRadius);
      outerGradient.addColorStop(0, '#b0bec5');
      outerGradient.addColorStop(1, '#78909c');
      this.ctx.beginPath();
      this.ctx.arc(this.centerX, this.centerY, this.outerRadius, 0, 2 * Math.PI);
      this.ctx.strokeStyle = outerGradient;
      this.ctx.lineWidth = 4;
      this.ctx.stroke();

      const questionText = selectedQuestion?.question_text || 'Yuklanmoqda...';
      this.ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
      this.ctx.fillRect(this.centerX - 250, 20, 500, 60);
      this.ctx.fillStyle = '#004d40';
      this.ctx.font = 'bold 24px Roboto';
      this.ctx.textAlign = 'center';
      this.ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';
      this.ctx.shadowBlur = 4;
      const lines = this.wrapText('Savol: ' + questionText, 500);
      lines.forEach((line, index) => {
        this.ctx.fillText(line, this.centerX, 50 + index * 30);
      });
      this.ctx.shadowBlur = 0;

      this.correctAnswerText = selectedQuestion?.answers.find(a => a.is_correct)?.text || 'Noma‘lum';

      const answers = selectedQuestion?.answers || [];
      for (let i = 0; i < sectorCount; i++) {
        const start = this.innerAngle + i * 2 * Math.PI / sectorCount;
        const end = start + 2 * Math.PI / sectorCount;
        const segmentGradient = this.ctx.createLinearGradient(
          this.centerX + Math.cos(start) * this.innerRadius,
          this.centerY + Math.sin(start) * this.innerRadius,
          this.centerX + Math.cos(end) * this.innerRadius,
          this.centerY + Math.sin(end) * this.innerRadius
        );
        segmentGradient.addColorStop(0, i % 2 ? '#90caf9' : '#b3e5fc');
        segmentGradient.addColorStop(1, i % 2 ? '#64b5f6' : '#81d4fa');
        this.ctx.beginPath();
        this.ctx.moveTo(this.centerX, this.centerY);
        this.ctx.arc(this.centerX, this.centerY, this.innerRadius, start, end);
        this.ctx.closePath();
        this.ctx.fillStyle = segmentGradient;
        this.ctx.fill();
        this.ctx.strokeStyle = '#455a64';
        this.ctx.lineWidth = 2;
        this.ctx.stroke();

        this.ctx.save();
        this.ctx.translate(this.centerX, this.centerY);
        this.ctx.rotate(start + Math.PI / sectorCount);
        this.ctx.textAlign = 'right';
        this.ctx.fillStyle = '#000';
        this.ctx.font = '16px Roboto';
        this.ctx.fillText(answers[i]?.text || '', this.innerRadius - 15, 5);
        this.ctx.restore();
      }
    },
    spin: async function() {
      if (this.isSpinning || !this.questions.length) {
        Swal.fire('Eslatma', 'Savollar yo‘q yoki aylantirish davom etmoqda.', 'warning');
        return;
      }
      if (this.questions.length <= 1) {
        Swal.fire('Eslatma', 'Oxirgi savol, aylantirish mumkin emas.', 'info');
        return;
      }

      this.isSpinning = true;
      const availableQuestions = this.questions.filter(q => !this.usedQuestionIds.includes(q.id));
      if (!availableQuestions.length) {
        Swal.fire('Xato', 'Yangi savollar topilmadi.', 'error');
        this.isSpinning = false;
        await this.fetchQuestions();
        return;
      }
      const questionIndex = Math.floor(Math.random() * availableQuestions.length);
      const question = availableQuestions[questionIndex];
      const actualIndex = this.questions.findIndex(q => q.id === question.id);
      this.usedQuestionIds.push(question.id);
      if (!question?.answers) {
        Swal.fire('Xato', 'Savol yuklanmadi.', 'error');
        this.isSpinning = false;
        return;
      }

      const correctAnswerIndex = question.answers.findIndex(a => a.is_correct);
      if (correctAnswerIndex === -1) {
        Swal.fire('Xato', 'To‘g‘ri javob yo‘q.', 'error');
        this.isSpinning = false;
        return;
      }

      const sectorCount = question.answers.length;
      const randomOuter = (actualIndex * (2 * Math.PI / sectorCount)) + (Math.random() * 0.1);
      const randomInner = (correctAnswerIndex * (2 * Math.PI / sectorCount)) + this.arrowAngle;
      const outerTarget = this.outerAngle + randomOuter + 2 * Math.PI;
      const innerTarget = this.innerAngle - randomInner;
      const duration = 1000;
      let startTime = null;

      const easeOutQuad = t => t * (2 - t) * 1.2;

      const animate = (time) => {
        if (!startTime) startTime = time;
        const progress = Math.min((time - startTime) / duration, 1);
        const easedProgress = easeOutQuad(progress);
        if (progress >= 1) {
          this.outerAngle = outerTarget;
          this.innerAngle = innerTarget;
          this.drawWheel();
          this.isSpinning = false;
          return;
        }
        this.outerAngle = this.outerAngle + (outerTarget - this.outerAngle) * easedProgress;
        this.innerAngle = this.innerAngle + (innerTarget - this.innerAngle) * easedProgress;
        this.drawWheel();
        requestAnimationFrame(animate);
      };
      requestAnimationFrame(animate);
    },
    rotateInner: function(dir) {
      if (!this.questions.length) return;
      const selectedQuestion = this.getSelectedQuestion();
      const sectorCount = selectedQuestion?.answers.length || 8;
      this.innerAngle += dir * (2 * Math.PI / sectorCount) / 8;
      this.drawWheel();
    },
    shuffleArray: function(array) {
      for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
      }
      return array;
    },
    getCsrfToken: function() {
      return document.cookie.split('; ').find(row => row.startsWith('csrftoken'))?.split('=')[1] || '';
    }
  }
});

app.mount('#app');