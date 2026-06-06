document.addEventListener('DOMContentLoaded', function () {

    const dateEl = document.getElementById('currentDate');
    if (dateEl) {
        const now = new Date();
        dateEl.textContent = now.toLocaleDateString('en-US', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' });
    }

    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const topbarToggle = document.getElementById('topbarToggle');

    function toggleSidebar() {
        if (!sidebar) return;
        if (window.innerWidth <= 768) {
            sidebar.classList.toggle('mobile-open');
        } else {
            sidebar.classList.toggle('collapsed');
        }
    }

    if (sidebarToggle) sidebarToggle.addEventListener('click', toggleSidebar);
    if (topbarToggle) topbarToggle.addEventListener('click', toggleSidebar);

    document.querySelectorAll('.close-alert').forEach(function (btn) {
        btn.addEventListener('click', function () {
            this.closest('.alert').style.opacity = '0';
            setTimeout(() => this.closest('.alert').remove(), 300);
        });
    });

    setTimeout(function () {
        document.querySelectorAll('.alert').forEach(function (alert) {
            alert.style.transition = 'opacity 0.4s';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 400);
        });
    }, 5000);

    document.querySelectorAll('.dept-bar').forEach(function (bar) {
        const target = bar.getAttribute('data-pct') || 0;
        bar.style.width = '0%';
        setTimeout(() => { bar.style.width = target + '%'; }, 200);
    });

    document.querySelectorAll('.progress-bar').forEach(function (bar) {
        const target = bar.getAttribute('data-pct') || 0;
        bar.style.width = '0%';
        setTimeout(() => { bar.style.width = Math.min(target, 100) + '%'; }, 300);
    });

    const roleSelect = document.getElementById('roleSelect');
    const studentFields = document.getElementById('studentFields');
    const companyFields = document.getElementById('companyFields');
    if (roleSelect) {
        function toggleFields() {
            const v = roleSelect.value;
            if (studentFields) studentFields.style.display = v === 'student' ? 'block' : 'none';
            if (companyFields) companyFields.style.display = v === 'company' ? 'block' : 'none';
        }
        roleSelect.addEventListener('change', toggleFields);
        toggleFields();
    }

    document.querySelectorAll('[data-modal]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const modalId = this.getAttribute('data-modal');
            const modal = document.getElementById(modalId);
            if (modal) {
                const aidField = modal.querySelector('[name="application_id"]');
                if (aidField && this.getAttribute('data-aid')) {
                    aidField.value = this.getAttribute('data-aid');
                }
                const jobField = modal.querySelector('[name="job_id"]');
                if (jobField && this.getAttribute('data-jid')) {
                    jobField.value = this.getAttribute('data-jid');
                }
                modal.classList.add('active');
            }
        });
    });

    document.querySelectorAll('.modal').forEach(function (modal) {
        modal.addEventListener('click', function (e) {
            if (e.target === modal) modal.classList.remove('active');
        });
    });

    document.querySelectorAll('.close-modal').forEach(function (btn) {
        btn.addEventListener('click', function () {
            this.closest('.modal').classList.remove('active');
        });
    });

    const searchInputs = document.querySelectorAll('.live-search');
    searchInputs.forEach(function (input) {
        input.addEventListener('input', function () {
            const val = this.value.toLowerCase();
            const target = document.querySelector(this.getAttribute('data-target'));
            if (!target) return;
            target.querySelectorAll('tbody tr').forEach(function (row) {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(val) ? '' : 'none';
            });
        });
    });

    document.querySelectorAll('form').forEach(function (form) {
        form.addEventListener('submit', function () {
            const btn = form.querySelector('button[type="submit"]');
            if (btn) {
                btn.disabled = true;
                const orig = btn.innerHTML;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
                setTimeout(() => { btn.disabled = false; btn.innerHTML = orig; }, 5000);
            }
        });
    });
});
