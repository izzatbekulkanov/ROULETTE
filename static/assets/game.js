const { createApp } = Vue;

const app = createApp({
  delimiters: ['[[', ']]'],
  data() {
    return {
      topicSlug: this.extractTopicSlug(),
      questions: [],
      currentQuestionIndex: 0,
      outerAngle: 0,
      innerAngle: 0,
      outerRadius: 270,
      innerRadius: 220,
      centerX: 300,
      centerY: 300,
      arrowAngle: Math.PI / 90,
      selectedAnswer: null,
      isSpinning: false,
      isLoading: false,
      isFading: false
    };
  },
  computed: {
    currentQuestion() {
      return this.questions[this.currentQuestionIndex] || null;
    }
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
          question_text: q.question_text || 'Savol matni yuklanmadi',
          answers: this.shuffleArray([...q.answers])
        }));
        this.currentQuestionIndex = 0;
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
    startSpinAnimation: function(spinCount) {
      this.isSpinning = true;
      this.isFading = true; // Savol matni uchun fade effekti
      this.selectedAnswer = null;
      const sectorCount = this.currentQuestion?.answers.length || 8;
      const randomSpins = Math.floor(Math.random() * (spinCount.max - spinCount.min + 1) + spinCount.min);
      const outerTarget = this.outerAngle + (randomSpins * 2 * Math.PI);
      const innerTarget = this.innerAngle + (Math.random() * 0.5 - 0.25) * 2 * Math.PI; // Engil tasodifiy ichki aylanish
      const duration = 2000; // 2 sekund
      let startTime = null;

      const easeOutQuint = t => 1 - Math.pow(1 - t, 5); // Realistik sekinlashuv

      const animate = (time) => {
        if (!startTime) startTime = time;
        const progress = Math.min((time - startTime) / duration, 1);
        const easedProgress = easeOutQuint(progress);
        if (progress >= 1) {
          this.outerAngle = outerTarget;
          this.innerAngle = innerTarget;
          this.drawWheel();
          this.isSpinning = false;
          this.isFading = false; // Fade effekti tugaydi
          return;
        }
        this.outerAngle = this.outerAngle + (outerTarget - this.outerAngle) * easedProgress;
        this.innerAngle = this.innerAngle + (innerTarget - this.innerAngle) * easedProgress;
        this.drawWheel();
        requestAnimationFrame(animate);
      };
      // Savol va javoblar darhol almashadi, fade effekti boshlanadi
      this.drawWheel();
      setTimeout(() => {
        this.isFading = false; // 500ms dan keyin fade effekti tugaydi
      }, 500);
      requestAnimationFrame(animate);
    },
    submitAnswer: async function() {
      if (!this.currentQuestion || !this.selectedAnswer) {
        Swal.fire('Xato', 'Javob tanlanmadi.', 'warning');
        return;
      }
      const answer = this.currentQuestion.answers.find(a => a.id === this.selectedAnswer);
      if (!answer) {
        Swal.fire('Xato', 'Javob topilmadi.', 'warning');
        return;
      }

      const result = await this.apiFetch('submit-answer/', {
        method: 'POST',
        body: JSON.stringify({ question_id: this.currentQuestion.id, answer_id: answer.id })
      });

      Swal.fire({
        icon: result.is_correct ? 'success' : 'error',
        title: result.is_correct ? '✅ To‘g‘ri!' : '❌ Noto‘g‘ri!',
        text: result.explanation
      }).then(() => {
        this.questions.splice(this.currentQuestionIndex, 1);
        if (this.questions.length === 0) {
          this.completeSession();
        } else {
          this.currentQuestionIndex = Math.min(this.currentQuestionIndex, this.questions.length - 1);
          this.startSpinAnimation({ min: 15, max: 20 }); // 15-20 aylanish
        }
      });
    },
    confirmCompleteSession: async function() {
      Swal.fire({
        title: 'Sessiyani yakunlashni xohlaysizmi?',
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: 'Ha',
        cancelButtonText: 'Yo‘q'
      }).then((result) => {
        if (result.isConfirmed) {
          this.completeSession();
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
    spin: function() {
      if (this.isSpinning || !this.questions.length) {
        Swal.fire('Eslatma', 'Savollar yo‘q yoki aylantirish davom etmoqda.', 'warning');
        return;
      }

      // Javob berilmagan savollarni topish
      const unansweredQuestions = this.questions.filter((q, index) => index > this.currentQuestionIndex);
      if (unansweredQuestions.length === 0) {
        // Agar joriy savol oxirgisi bo'lsa, boshidan boshlash
        if (this.currentQuestionIndex >= this.questions.length - 1) {
          this.currentQuestionIndex = 0;
        } else {
          Swal.fire('Eslatma', 'Javob berilmagan savollar yo‘q.', 'info');
          return;
        }
      } else {
        // Keyingi javob berilmagan savolga o'tish
        this.currentQuestionIndex++;
      }

      this.startSpinAnimation({ min: 10, max: 15 }); // 10-15 aylanish
    },
    rotateInner: function(dir) {
      if (!this.currentQuestion) return;
      const sectorCount = this.currentQuestion.answers.length || 8;
      this.innerAngle += dir * (2 * Math.PI / sectorCount) / 8;
      const answerIndex = this.getIndex(this.innerAngle, sectorCount);
      this.selectedAnswer = this.currentQuestion.answers[answerIndex]?.id || null;
      this.drawWheel();
    },
    getIndex: function(angle, sectorCount) {
      return Math.floor(((-angle % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI) / (2 * Math.PI / sectorCount));
    },
    wrapText: function(text, maxWidth) {
      if (!text) return [''];
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
      if (lines.length > 2) {
        lines = lines.slice(0, 2);
        lines[1] = lines[1].substring(0, 20) + '...';
      }
      return lines;
    },
    drawWheel: function() {
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
      if (!this.currentQuestion) {
        this.ctx.fillStyle = '#004d40';
        this.ctx.font = 'bold 24px Roboto';
        this.ctx.textAlign = 'center';
        this.ctx.fillText('Savollar tayyorlanmoqda...', this.centerX, this.centerY);
        return;
      }
      const sectorCount = this.currentQuestion.answers.length || 8;

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

      const answers = this.currentQuestion.answers || [];
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
        this.ctx.font = '14px Roboto';
        const lines = this.wrapText(answers[i]?.text || '', 100);
        lines.forEach((line, index) => {
          this.ctx.fillText(line, this.innerRadius - 15, 5 + index * 16);
        });
        this.ctx.restore();
      }
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