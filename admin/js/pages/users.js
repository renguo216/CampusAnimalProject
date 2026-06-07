const UsersPage = {
    currentPage: 1,
    pageSize: 20,
    users: [],

    async render() {
        const content = document.getElementById('pageContent');
        content.innerHTML = App.showLoading();
        await this.loadData();
    },

    async loadData() {
        const content = document.getElementById('pageContent');
        
        try {
            const result = await Api.user.getAll(this.currentPage, this.pageSize);
            
            if (result.success) {
                this.users = result.data.users || [];
                content.innerHTML = this.renderContent();
            } else {
                content.innerHTML = `
                    <div class="card">
                        <div class="card-body">
                            ${App.showEmpty('⚠️', result.message || '获取用户列表失败')}
                        </div>
                    </div>
                `;
            }
        } catch (error) {
            content.innerHTML = `
                <div class="card">
                    <div class="card-body">
                        ${App.showEmpty('❌', '网络错误')}
                    </div>
                </div>
            `;
        }
    },

    renderContent() {
        if (this.users.length === 0) {
            return `
                <div class="card">
                    <div class="card-body">
                        ${App.showEmpty('👥', '暂无用户数据')}
                    </div>
                </div>
            `;
        }

        return `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">用户列表</h3>
                    <span style="color: var(--text-light);">共 ${this.users.length} 个用户</span>
                </div>
                <div class="card-body">
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>用户ID</th>
                                    <th>昵称</th>
                                    <th>角色</th>
                                    <th>积分</th>
                                    <th>获赞</th>
                                    <th>粉丝</th>
                                    <th>状态</th>
                                    <th>注册时间</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${this.users.map(user => this.renderRow(user)).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
    },

    renderRow(user) {
        const isActive = user.is_active !== 0;
        return `
            <tr>
                <td><span class="text-truncate" title="${user.user_id}">${user.user_id.substring(0, 8)}...</span></td>
                <td>${user.nickname || '-'}</td>
                <td>${App.formatRole(user.role)}</td>
                <td>${user.points || 0}</td>
                <td>${user.like_count || 0}</td>
                <td>${user.follower_count || 0}</td>
                <td>
                    <span class="status-badge ${isActive ? 'status-active' : 'status-inactive'}">
                        ${isActive ? '正常' : '封禁'}
                    </span>
                </td>
                <td>${App.formatDateTime(user.created_at)}</td>
                <td>
                    <div class="action-btns">
                        <button class="btn btn-sm btn-primary" onclick="UsersPage.showEditRole('${user.user_id}', ${user.role})">
                            修改角色
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="UsersPage.showDeleteConfirm('${user.user_id}', '${user.nickname}')">
                            删除
                        </button>
                    </div>
                </td>
            </tr>
        `;
    },

    showEditRole(userId, currentRole) {
        App.showModal('修改用户角色', `
            <div class="form-group">
                <label>用户ID</label>
                <input type="text" value="${userId}" disabled>
            </div>
            <div class="form-group">
                <label>当前角色</label>
                <input type="text" value="${currentRole === 1 ? '普通用户' : currentRole === 2 ? '志愿者' : '管理员'}" disabled>
            </div>
            <div class="form-group">
                <label>新角色</label>
                <select id="newRole">
                    <option value="1" ${currentRole === 1 ? 'selected' : ''}>普通用户</option>
                    <option value="2" ${currentRole === 2 ? 'selected' : ''}>志愿者</option>
                    <option value="3" ${currentRole === 3 ? 'selected' : ''}>管理员</option>
                </select>
            </div>
        `, [
            { text: '取消', class: 'btn-danger', onClick: () => App.hideModal() },
            { text: '确认修改', class: 'btn-primary', onClick: () => this.updateRole(userId) }
        ]);
    },

    async updateRole(userId) {
        const newRole = parseInt(document.getElementById('newRole').value);
        
        try {
            const result = await Api.user.updateRole(userId, newRole);
            
            if (result.success) {
                App.showToast('角色修改成功', 'success');
                App.hideModal();
                this.loadData();
            } else {
                App.showToast(result.message || '修改失败', 'error');
            }
        } catch (error) {
            App.showToast('网络错误', 'error');
        }
    },

    showDeleteConfirm(userId, nickname) {
        App.showModal('删除用户确认', `
            <div class="alert alert-danger">
                <p>确定要删除用户 <strong>${nickname}</strong> 吗？</p>
                <p style="font-size: 0.9rem; margin-top: 0.5rem;">此操作不可逆！</p>
            </div>
        `, [
            { text: '取消', class: 'btn-primary', onClick: () => App.hideModal() },
            { text: '确认删除', class: 'btn-danger', onClick: () => this.deleteUser(userId) }
        ]);
    },

    async deleteUser(userId) {
        try {
            const result = await Api.user.delete(userId);
            
            if (result.success) {
                App.showToast('用户已删除', 'success');
                App.hideModal();
                this.loadData();
            } else {
                App.showToast(result.message || '删除失败', 'error');
            }
        } catch (error) {
            App.showToast('网络错误', 'error');
        }
    },

    async goToPage(page) {
        this.currentPage = page;
        await this.loadData();
    }
};
