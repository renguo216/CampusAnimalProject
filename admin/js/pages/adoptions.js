const AdoptionsPage = {
    currentPage: 1,
    pageSize: 20,
    applications: [],
    total: 0,
    petIdFilter: 1,

    async render() {
        const content = document.getElementById('pageContent');
        content.innerHTML = App.showLoading();
        await this.loadData();
    },

    async loadData() {
        const content = document.getElementById('pageContent');
        
        try {
            const result = await Api.admin.getAdoptions(this.petIdFilter, this.currentPage, this.pageSize);
            
            if (result.success) {
                this.applications = result.data.applications || [];
                this.total = result.data.total || 0;
                content.innerHTML = this.renderContent();
            } else {
                content.innerHTML = `
                    <div class="card">
                        <div class="card-body">
                            ${App.showEmpty('⚠️', result.message || '获取领养申请列表失败')}
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
        if (this.applications.length === 0) {
            return `
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">领养申请列表</h3>
                    </div>
                    <div class="card-body">
                        <div class="filter-bar">
                            <label style="color: var(--text-light);">动物ID：</label>
                            <input type="number" id="petIdFilter" value="${this.petIdFilter}" min="1" style="width: 100px;" onchange="AdoptionsPage.filterByPetId()">
                            <button class="btn btn-primary btn-sm" onclick="AdoptionsPage.filterByPetId()">查询</button>
                        </div>
                        ${App.showEmpty('🏠', '暂无领养申请')}
                    </div>
                </div>
            `;
        }

        const totalPages = Math.ceil(this.total / this.pageSize);

        return `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">领养申请列表</h3>
                    <span style="color: var(--text-light);">共 ${this.total} 条记录</span>
                </div>
                <div class="card-body">
                    <div class="filter-bar">
                        <label style="color: var(--text-light);">动物ID：</label>
                        <input type="number" id="petIdFilter" value="${this.petIdFilter}" min="1" style="width: 100px;" onchange="AdoptionsPage.filterByPetId()">
                        <button class="btn btn-primary btn-sm" onclick="AdoptionsPage.filterByPetId()">查询</button>
                    </div>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>申请单号</th>
                                    <th>动物ID</th>
                                    <th>申请人</th>
                                    <th>申请理由</th>
                                    <th>状态</th>
                                    <th>申请时间</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${this.applications.map(app => this.renderRow(app)).join('')}
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
                <td><span class="text-truncate" title="${app.apply_id}">${app.apply_id.substring(0, 10)}...</span></td>
                <td>${app.pet_id}</td>
                <td><span class="text-truncate" title="${app.user_id}">${app.user_id ? app.user_id.substring(0, 8) + '...' : '-'}</span></td>
                <td><span class="text-truncate" title="${app.content || ''}">${app.content ? app.content.substring(0, 20) + '...' : '-'}</span></td>
                <td>${App.formatStatus(app.status, 'adoption')}</td>
                <td>${App.formatDateTime(app.created_at)}</td>
                <td>
                    <div class="action-btns">
                        ${app.status === 0 ? `
                            <button class="btn btn-sm btn-success" onclick="AdoptionsPage.showApprove('${app.apply_id}')">
                                通过
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="AdoptionsPage.showReject('${app.apply_id}')">
                                驳回
                            </button>
                        ` : `
                            <button class="btn btn-sm btn-warning" onclick="AdoptionsPage.showDetail('${app.apply_id}')">
                                详情
                            </button>
                        `}
                        <button class="btn btn-sm btn-info" onclick="AdoptionsPage.showEdit('${app.apply_id}')">
                            编辑
                        </button>
                    </div>
                </td>
            </tr>
        `;
    },

    renderPagination(totalPages) {
        let html = '<div class="pagination">';
        html += `<button ${this.currentPage <= 1 ? 'disabled' : ''} onclick="AdoptionsPage.goToPage(${this.currentPage - 1})">上一页</button>`;
        
        const startPage = Math.max(1, this.currentPage - 2);
        const endPage = Math.min(totalPages, this.currentPage + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            html += `<button class="${i === this.currentPage ? 'active' : ''}" onclick="AdoptionsPage.goToPage(${i})">${i}</button>`;
        }
        
        html += `<button ${this.currentPage >= totalPages ? 'disabled' : ''} onclick="AdoptionsPage.goToPage(${this.currentPage + 1})">下一页</button>`;
        html += '</div>';
        return html;
    },

    async filterByPetId() {
        const petId = parseInt(document.getElementById('petIdFilter').value) || 1;
        this.petIdFilter = petId;
        this.currentPage = 1;
        await this.loadData();
    },

    showApprove(applyId) {
        App.showModal('批准领养申请', `
            <div class="form-group">
                <label>申请单号</label>
                <input type="text" value="${applyId}" disabled>
            </div>
            <div class="form-group">
                <label>审核意见（可选）</label>
                <textarea id="reviewComment" placeholder="请输入审核意见"></textarea>
            </div>
        `, [
            { text: '取消', class: 'btn-danger', onClick: () => App.hideModal() },
            { text: '确认通过', class: 'btn-success', onClick: () => this.approve(applyId) }
        ]);
    },

    async approve(applyId) {
        const reviewComment = document.getElementById('reviewComment').value.trim();
        
        try {
            const result = await Api.adoption.approve(applyId, reviewComment);
            
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

    showReject(applyId) {
        App.showModal('驳回领养申请', `
            <div class="form-group">
                <label>申请单号</label>
                <input type="text" value="${applyId}" disabled>
            </div>
            <div class="form-group">
                <label>驳回原因</label>
                <textarea id="reviewComment" placeholder="请输入驳回原因"></textarea>
            </div>
        `, [
            { text: '取消', class: 'btn-danger', onClick: () => App.hideModal() },
            { text: '确认驳回', class: 'btn-primary', onClick: () => this.reject(applyId) }
        ]);
    },

    async reject(applyId) {
        const reviewComment = document.getElementById('reviewComment').value.trim();
        
        try {
            const result = await Api.adoption.reject(applyId, reviewComment);
            
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

    showDetail(applyId) {
        const app = this.applications.find(a => a.apply_id === applyId);
        if (!app) {
            App.showToast('未找到记录', 'error');
            return;
        }

        App.showModal('申请详情', `
            <div class="form-group">
                <label>申请单号</label>
                <input type="text" value="${app.apply_id}" disabled>
            </div>
            <div class="form-group">
                <label>动物ID</label>
                <input type="text" value="${app.pet_id}" disabled>
            </div>
            <div class="form-group">
                <label>申请人ID</label>
                <input type="text" value="${app.user_id || '-'}" disabled>
            </div>
            <div class="form-group">
                <label>申请理由</label>
                <textarea disabled>${app.content || '-'}</textarea>
            </div>
            <div class="form-group">
                <label>状态</label>
                <input type="text" value="${['审核中', '已通过', '已驳回'][app.status] || '未知'}" disabled>
            </div>
            <div class="form-group">
                <label>申请时间</label>
                <input type="text" value="${App.formatDateTime(app.created_at)}" disabled>
            </div>
            <div class="form-group">
                <label>审核意见</label>
                <textarea disabled>${app.review_comment || '-'}</textarea>
            </div>
        `, [
            { text: '关闭', class: 'btn-primary', onClick: () => App.hideModal() }
        ]);
    },

    showEdit(applyId) {
        const app = this.applications.find(a => a.apply_id === applyId);
        if (!app) {
            App.showToast('未找到记录', 'error');
            return;
        }

        App.showModal('编辑领养申请', `
            <div class="form-group">
                <label>申请单号</label>
                <input type="text" value="${app.apply_id}" disabled>
            </div>
            <div class="form-group">
                <label>动物ID</label>
                <input type="text" value="${app.pet_id}" disabled>
            </div>
            <div class="form-group">
                <label>申请人ID</label>
                <input type="text" value="${app.user_id || '-'}" disabled>
            </div>
            <div class="form-group">
                <label>状态</label>
                <select id="editStatus">
                    <option value="0" ${app.status === 0 ? 'selected' : ''}>审核中</option>
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
            { text: '保存', class: 'btn-primary', onClick: () => this.edit(applyId) }
        ]);
    },

    async edit(applyId) {
        const status = parseInt(document.getElementById('editStatus').value);
        const reviewComment = document.getElementById('editReviewComment').value.trim();
        
        try {
            const result = await Api.adoption.update(applyId, status, reviewComment);
            
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
