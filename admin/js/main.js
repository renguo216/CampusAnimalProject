const App = {
    currentPage: 'dashboard',
    pages: {},

    init() {
        this.registerPages();
        this.bindEvents();
        this.checkAuth();
    },

    registerPages() {
        this.pages = {
            dashboard: DashboardPage,
            users: UsersPage,
            animals: AnimalsPage,
            donations: DonationsPage,
            volunteers: VolunteersPage,
            adoptions: AdoptionsPage,
            rescues: RescuesPage,
            products: ProductPage,
            posts: PostPage
        };
    },

    bindEvents() {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const page = item.dataset.page;
                this.navigateTo(page);
            });
        });

        document.getElementById('btnLogout').addEventListener('click', () => {
            this.logout();
        });

        document.getElementById('modalClose').addEventListener('click', () => {
            this.hideModal();
        });

        document.getElementById('modal').addEventListener('click', (e) => {
            if (e.target.id === 'modal') {
                this.hideModal();
            }
        });
    },

    checkAuth() {
        const savedUserId = localStorage.getItem('admin_user_id');
        if (savedUserId) {
            Api.user.getUser(savedUserId).then(result => {
                if (result.success && result.data) {
                    if (result.data.role === 3) {
                        document.getElementById('adminName').textContent = result.data.nickname || '管理员';
                        Api.setToken(savedUserId);
                        this.navigateTo('dashboard');
                    } else {
                        this.showLoginPrompt();
                    }
                } else {
                    this.showLoginPrompt();
                }
            });
        } else {
            this.showLoginPrompt();
        }
    },

    showLoginPrompt() {
        this.showModal('管理员登录', `
            <div class="form-group">
                <label>用户ID</label>
                <input type="text" id="loginUserId" placeholder="请输入管理员用户ID">
            </div>
        `, [
            { text: '登录', class: 'btn-primary', onClick: () => this.handleLogin() }
        ]);
    },

    async handleLogin() {
        const userId = document.getElementById('loginUserId').value.trim();
        if (!userId) {
            this.showToast('请输入用户ID', 'error');
            return;
        }

        const result = await Api.user.getUser(userId);
        if (result.success && result.data) {
            if (result.data.role === 3) {
                localStorage.setItem('admin_user_id', userId);
                Api.setToken(userId);
                document.getElementById('adminName').textContent = result.data.nickname || '管理员';
                this.hideModal();
                this.navigateTo('dashboard');
                this.showToast('登录成功', 'success');
            } else {
                this.showToast('该用户不是管理员', 'error');
            }
        } else {
            this.showToast('用户不存在', 'error');
        }
    },

    logout() {
        Api.clearToken();
        localStorage.removeItem('admin_user_id');
        document.getElementById('adminName').textContent = '管理员';
        this.showLoginPrompt();
        this.showToast('已退出登录', 'success');
    },

    navigateTo(page) {
        if (!this.pages[page]) {
            console.error('页面不存在:', page);
            return;
        }

        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.page === page) {
                item.classList.add('active');
            }
        });

        const titles = {
            dashboard: '仪表盘',
            users: '用户管理',
            animals: '动物管理',
            donations: '捐款管理',
            volunteers: '志愿者管理',
            adoptions: '领养管理',
            rescues: '救助管理'
        };

        document.getElementById('pageTitle').textContent = titles[page] || page;
        this.currentPage = page;
        this.pages[page].render();
    },

    showModal(title, bodyHtml, buttons = []) {
        document.getElementById('modalTitle').textContent = title;
        document.getElementById('modalBody').innerHTML = bodyHtml;
        
        const footer = document.getElementById('modalFooter');
        footer.innerHTML = '';
        
        buttons.forEach(btn => {
            const button = document.createElement('button');
            button.className = `btn ${btn.class || 'btn-primary'}`;
            button.textContent = btn.text;
            button.addEventListener('click', btn.onClick);
            footer.appendChild(button);
        });
        
        document.getElementById('modal').classList.add('show');
    },

    hideModal() {
        document.getElementById('modal').classList.remove('show');
    },

    showToast(message, type = 'success') {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = `toast show ${type}`;
        
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    },

    showLoading() {
        return '<div class="loading"></div>';
    },

    showEmpty(icon = '📭', text = '暂无数据') {
        return `
            <div class="empty-state">
                <div class="icon">${icon}</div>
                <div class="text">${text}</div>
            </div>
        `;
    },

    formatDateTime(dateStr) {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    formatStatus(status, type) {
        const statusMap = {
            adoption: {
                0: { text: '审核中', class: 'status-pending' },
                1: { text: '已通过', class: 'status-approved' },
                2: { text: '已驳回', class: 'status-rejected' }
            },
            donation: {
                0: { text: '待确认', class: 'status-pending' },
                1: { text: '已到账', class: 'status-approved' },
                2: { text: '已驳回', class: 'status-rejected' },
                3: { text: '已取消', class: 'status-inactive' }
            },
            volunteer: {
                0: { text: '待审核', class: 'status-pending' },
                1: { text: '已通过', class: 'status-approved' },
                2: { text: '已驳回', class: 'status-rejected' }
            },
            animal: {
                0: { text: '在校', class: 'status-active' },
                1: { text: '已领养', class: 'status-approved' },
                2: { text: '需医疗', class: 'status-pending' }
            },
            rescue: {
                0: { text: '待接单', class: 'status-pending' },
                1: { text: '救助中', class: 'status-active' },
                2: { text: '待确认', class: 'status-pending' },
                3: { text: '已完成', class: 'status-approved' },
                4: { text: '已关闭', class: 'status-inactive' }
            },
            exchange: {
                0: { text: '待发货', class: 'status-pending' },
                1: { text: '已完成', class: 'status-approved' },
                2: { text: '已取消', class: 'status-inactive' }
            }
        };

        const map = statusMap[type] || {};
        const info = map[status] || { text: '未知', class: 'status-pending' };
        return `<span class="status-badge ${info.class}">${info.text}</span>`;
    },

    formatRole(role) {
        const roleMap = {
            1: { text: '普通用户', class: 'role-user' },
            2: { text: '志愿者', class: 'role-volunteer' },
            3: { text: '管理员', class: 'role-admin' }
        };
        const info = roleMap[role] || { text: '未知', class: 'role-user' };
        return `<span class="role-badge ${info.class}">${info.text}</span>`;
    },

    renderPagination(currentPage, totalPages, onPageChange) {
        if (totalPages <= 1) return '';
        
        let html = '<div class="pagination">';
        
        html += `<button ${currentPage <= 1 ? 'disabled' : ''} onclick="${onPageChange}(${currentPage - 1})">上一页</button>`;
        
        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, currentPage + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            html += `<button class="${i === currentPage ? 'active' : ''}" onclick="${onPageChange}(${i})">${i}</button>`;
        }
        
        html += `<button ${currentPage >= totalPages ? 'disabled' : ''} onclick="${onPageChange}(${currentPage + 1})">下一页</button>`;
        
        html += '</div>';
        return html;
    }
};

document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
