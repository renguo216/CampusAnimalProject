const VolunteersPage = {
    currentPage: 1,
    pageSize: 20,
    applications: [],
    total: 0,
    statusFilter: '',

    async render() {
        const content = document.getElementById('pageContent');
        content.innerHTML = App.showLoading();
        await this.loadData();
    },

    async loadData() {
        const content = document.getElementById('pageContent');
        
        try {
            const result = await Api.admin.getVolunteers(this.currentPage, this.pageSize);
            
            if (result.success) {
                this.applications = result.data.applications || [];
                this.total = result.data.total || 0;
                content.innerHTML = this.renderContent();
            } else {
                content.innerHTML = `
                    <div class="card">
                        <div class="card-body">
                            ${App.showEmpty('⚠️', result.message || '获取志愿者申请列表失败')}
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
        let filteredApplications = this.applications;
        if (this.statusFilter !== '') {
            filteredApplications = this.applications.filter(a => a.status === parseInt(this.statusFilter));
        }

        if (filteredApplications.length === 0 && this.applications.length === 0) {
            return `
                <div class="card">
                    <div class="card-body">
                        ${App.showEmpty('🙋', '暂无志愿者申请')}
                    </div>
                </div>
            `;
        }

        const totalPages = Math.ceil(this.total / this.pageSize);

        return `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">志愿者申请列表</h3>
                    <span style="color: var(--text-light);">共 ${this.total} 条记录</span>
                </div>
                <div class="card-body">
                    <div class="filter-bar">
                        <select id="statusFilter" onchange="VolunteersPage.filterByStatus()">
                            <option value="">全部状态</option>
                            <option value="0" ${this.statusFilter === '0' ? 'selected' : ''}>待审核</option>
                            <option value="1" ${this.statusFilter === '1' ? 'selected' : ''}>已通过</option>
                            <option value="2" ${this.statusFilter === '2' ? 'selected' : ''}>已驳回</option>
                        </select>
                    </div>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>申请ID</th>
                                    <th>申请人</th>
                                    <th>申请理由</th>
                                    <th>状态</th>
                                    <th>申请时间</th>
                                    <th>审核人</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${filteredApplications.map(app => this.renderRow(app)).join('')}
                            </tbody>
                        </table>
                    </div>
                    ${totalPages > 1 ? this.renderPagination(totalPages) : ''}
                </div>
            </div>
        `;
    },

    renderRow(app) {
        return `
            <tr>
                <td>${app.application_id}</td>
                <td><span class="text-truncate" title="${app.user_id}">${app.user_id ? app.user_id.substring(0, 8) + '...' : '-'}</span></td>
                <td><span class="text-truncate" title="${app.apply_content || ''}">${app.apply_content ? app.apply_content.substring(0, 20) + '...' : '-'}</span></td>
                <td>${App.formatStatus(app.status, 'volunteer')}</td>
                <td>${App.formatDateTime(app.created_at)}</td>
                <td>${app.reviewed_by ? app.reviewed_by.substring(0, 8) + '...' : '-'}</td>
                <td>
                    <div class="action-btns">
                        ${app.status === 0 ? `
                            <button class="btn btn-sm btn-success" onclick="VolunteersPage.showApprove(${app.application_id})">
                                通过
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="VolunteersPage.showReject(${app.application_id})">
                                驳回
                            </button>
                        ` : `
                            <button class="btn btn-sm btn-warning" onclick="VolunteersPage.showDetail(${app.application_id})">
                                详情
                            </button>
                        `}
                        <button class="btn btn-sm btn-info" onclick="VolunteersPage.showEdit(${app.application_id})">
                            编辑
                        </button>
                    </div>
                </td>
            </tr>
        `;
    },

    renderPagination(totalPages) {
        let html = '<div class="pagination">';
        html += `<button ${this.currentPage <= 1 ? 'disabled' : ''} onclick="VolunteersPage.goToPage(${this.currentPage - 1})">上一页</button>`;
        
        const startPage = Math.max(1, this.currentPage - 2);
        const endPage = Math.min(totalPages, this.currentPage + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            html += `<button class="${i === this.currentPage ? 'active' : ''}" onclick="VolunteersPage.goToPage(${i})">${i}</button>`;
        }
        
        html += `<button ${this.currentPage >= totalPages ? 'disabled' : ''} onclick="VolunteersPage.goToPage(${this.currentPage + 1})">下一页</button>`;
        html += '</div>';
        return html;
    },

    filterByStatus() {
        this.statusFilter = document.getElementById('statusFilter').value;
        const content = document.getElementById('pageContent');
        content.innerHTML = this.renderContent();
    },

    showApprove(applicationId) {
        App.showModal('批准志愿者申请', `
            <div class="form-group">
                <label>申请ID</label>
                <input type="text" value="${applicationId}" disabled>
            </div>
            <div class="form-group">
                <label>审核意见（可选）</label>
                <textarea id="reviewComment" placeholder="请输入审核意见"></textarea>
            </div>
        `, [
            { text: '取消', class: 'btn-danger', onClick: () => App.hideModal() },
            { text: '确认通过', class: 'btn-success', onClick: () => this.approve(applicationId) }
        ]);
    },

    async approve(applicationId) {
        const reviewComment = document.getElementById('reviewComment').value.trim();
        try {
            const result = await Api.volunteer.approve(applicationId, reviewComment);
            if (result.success) {
                App.showToast('批准成功', 'success');
                App.hideModal();
                this.loadData();
            } else {
                App.showToast(result.message || '操作失败', 'error');
            }
        } catch (error) {
            App.showToast('网络错误', 'error');
        }
    },

    showReject(applicationId) {
        App.showModal('驳回志愿者申请', `
            <div class="form-group">
                <label>申请ID</label>
                <input type="text" value="${applicationId}" disabled>
            </div>
            <div class="form-group">
                <label>驳回原因</label>
                <textarea id="rejectReason" placeholder="请输入驳回原因"></textarea>
            </div>
        `, [
            { text: '取消', class: 'btn-danger', onClick: () => App.hideModal() },
            { text: '确认驳回', class: 'btn-primary', onClick: () => this.reject(applicationId) }
        ]);
    },

    async reject(applicationId) {
        const reason = document.getElementById('rejectReason').value.trim();
        
        try {
            const result = await Api.volunteer.reject(applicationId, reason);
            
            if (result.success) {
                App.showToast('驳回成功', 'success');
                App.hideModal();
                this.loadData();
            } else {
                App.showToast(result.message || '操作失败', 'error');
            }
        } catch (error) {
            App.showToast('网络错误', 'error');
        }
    },

    showDetail(applicationId) {
        const app = this.applications.find(a => a.application_id === applicationId);
        if (!app) {
            App.showToast('未找到记录', 'error');
            return;
        }

        App.showModal('申请详情', `
            <div class="form-group">
                <label>申请ID</label>
                <input type="text" value="${app.application_id}" disabled>
            </div>
            <div class="form-group">
                <label>申请人ID</label>
                <input type="text" value="${app.user_id || '-'}" disabled>
            </div>
            <div class="form-group">
                <label>申请理由</label>
                <textarea disabled>${app.apply_content || '-'}</textarea>
            </div>
            <div class="form-group">
                <label>状态</label>
                <input type="text" value="${['待审核', '已通过', '已驳回'][app.status] || '未知'}" disabled>
            </div>
            <div class="form-group">
                <label>申请时间</label>
                <input type="text" value="${App.formatDateTime(app.created_at)}" disabled>
            </div>
            <div class="form-group">
                <label>审核人ID</label>
                <input type="text" value="${app.reviewed_by || '-'}" disabled>
            </div>
            <div class="form-group">
                <label>审核时间</label>
                <input type="text" value="${App.formatDateTime(app.reviewed_at)}" disabled>
            </div>
            <div class="form-group">
                <label>审核意见</label>
                <textarea disabled>${app.review_comment || '-'}</textarea>
            </div>
        `, [
            { text: '关闭', class: 'btn-primary', onClick: () => App.hideModal() }
        ]);
    },

    showEdit(applicationId) {
        const app = this.applications.find(a => a.application_id === applicationId);
        if (!app) {
            App.showToast('未找到记录', 'error');
            return;
        }

        App.showModal('编辑志愿者申请', `
            <div class="form-group">
                <label>申请ID</label>
                <input type="text" value="${app.application_id}" disabled>
            </div>
            <div class="form-group">
                <label>申请人ID</label>
                <input type="text" value="${app.user_id || '-'}" disabled>
            </div>
            <div class="form-group">
                <label>状态</label>
                <select id="editStatus">
                    <option value="0" ${app.status === 0 ? 'selected' : ''}>待审核</option>
                    <option value="1" ${app.status === 1 ? 'selected' : ''}>已通过</option>
                    <option value="2" ${app.status === 2 ? 'selected' : ''}>已驳回</option>
                </select>
            </div>
            <div class="form-group">
                <label>审核意见</label>
                <textarea id="editReviewComment" placeholder="请输入审核意见">${app.review_comment || ''}</textarea>
            </div>
        `, [
            { text: '取消', class: 'btn-danger', onClick: () => App.hideModal() },
            { text: '保存', class: 'btn-primary', onClick: () => this.edit(applicationId) }
        ]);
    },

    async edit(applicationId) {
        const status = parseInt(document.getElementById('editStatus').value);
        const reviewComment = document.getElementById('editReviewComment').value.trim();
        
        try {
            const result = await Api.admin.updateVolunteer(applicationId, status, reviewComment);
            
            if (result.success) {
                App.showToast('修改成功', 'success');
                App.hideModal();
                this.loadData();
            } else {
                App.showToast(result.message || '操作失败', 'error');
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
