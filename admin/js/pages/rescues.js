const RescuesPage = {
    currentPage: 1,
    pageSize: 20,
    records: [],
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
            const result = await Api.admin.getRescues(this.currentPage, this.pageSize);
            
            if (result.success) {
                this.records = result.data.records || [];
                this.total = result.data.total || 0;
                content.innerHTML = this.renderContent();
            } else {
                content.innerHTML = `
                    <div class="card">
                        <div class="card-body">
                            ${App.showEmpty('⚠️', result.message || '获取救助记录列表失败')}
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
        let filteredRecords = this.records;
        if (this.statusFilter !== '') {
            filteredRecords = this.records.filter(r => r.status === parseInt(this.statusFilter));
        }

        if (filteredRecords.length === 0 && this.records.length === 0) {
            return `
                <div class="card">
                    <div class="card-body">
                        ${App.showEmpty('🚑', '暂无救助记录')}
                    </div>
                </div>
            `;
        }

        const totalPages = Math.ceil(this.total / this.pageSize);

        return `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">救助记录列表</h3>
                    <span style="color: var(--text-light);">共 ${this.total} 条记录</span>
                </div>
                <div class="card-body">
                    <div class="filter-bar">
                        <select id="statusFilter" onchange="RescuesPage.filterByStatus()">
                            <option value="">全部状态</option>
                            <option value="0" ${this.statusFilter === '0' ? 'selected' : ''}>待接单</option>
                            <option value="1" ${this.statusFilter === '1' ? 'selected' : ''}>救助中</option>
                            <option value="2" ${this.statusFilter === '2' ? 'selected' : ''}>待确认</option>
                            <option value="3" ${this.statusFilter === '3' ? 'selected' : ''}>已完成</option>
                            <option value="4" ${this.statusFilter === '4' ? 'selected' : ''}>已关闭</option>
                        </select>
                    </div>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>记录编号</th>
                                    <th>标题</th>
                                    <th>上报人</th>
                                    <th>接单志愿者</th>
                                    <th>位置</th>
                                    <th>优先级</th>
                                    <th>状态</th>
                                    <th>创建时间</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${filteredRecords.map(record => this.renderRow(record)).join('')}
                            </tbody>
                        </table>
                    </div>
                    ${totalPages > 1 ? this.renderPagination(totalPages) : ''}
                </div>
            </div>
        `;
    },

    renderRow(record) {
        const priorityMap = { 0: '普通', 1: '紧急', 2: '非常紧急' };
        const priorityClass = { 0: '', 1: 'style="color: var(--warning-color); font-weight: 600;"', 2: 'style="color: var(--danger-color); font-weight: 600;"' };
        
        return `
            <tr>
                <td><span class="text-truncate" title="${record.record_id}">${record.record_id.substring(0, 8)}...</span></td>
                <td>${record.title || '-'}</td>
                <td><span class="text-truncate" title="${record.user_id}">${record.user_id ? record.user_id.substring(0, 8) + '...' : '-'}</span></td>
                <td>${record.helper_id ? record.helper_id.substring(0, 8) + '...' : '-'}</td>
                <td><span class="text-truncate" title="${record.found_location_text || ''}">${record.found_location_text ? record.found_location_text.substring(0, 15) + '...' : '-'}</span></td>
                <td ${priorityClass[record.priority] || ''}>${priorityMap[record.priority] || '普通'}</td>
                <td>${App.formatStatus(record.status, 'rescue')}</td>
                <td>${App.formatDateTime(record.created_at)}</td>
                <td>
                    <div class="action-btns">
                        <button class="btn btn-sm btn-warning" onclick="RescuesPage.showDetail('${record.record_id}')">
                            详情
                        </button>
                    </div>
                </td>
            </tr>
        `;
    },

    renderPagination(totalPages) {
        let html = '<div class="pagination">';
        html += `<button ${this.currentPage <= 1 ? 'disabled' : ''} onclick="RescuesPage.goToPage(${this.currentPage - 1})">上一页</button>`;
        
        const startPage = Math.max(1, this.currentPage - 2);
        const endPage = Math.min(totalPages, this.currentPage + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            html += `<button class="${i === this.currentPage ? 'active' : ''}" onclick="RescuesPage.goToPage(${i})">${i}</button>`;
        }
        
        html += `<button ${this.currentPage >= totalPages ? 'disabled' : ''} onclick="RescuesPage.goToPage(${this.currentPage + 1})">下一页</button>`;
        html += '</div>';
        return html;
    },

    filterByStatus() {
        this.statusFilter = document.getElementById('statusFilter').value;
        const content = document.getElementById('pageContent');
        content.innerHTML = this.renderContent();
    },

    async showDetail(recordId) {
        try {
            const result = await Api.rescue.getById(recordId);
            
            if (result.success && result.data) {
                const record = result.data;
                const priorityMap = { 0: '普通', 1: '紧急', 2: '非常紧急' };
                const statusMap = { 0: '待接单', 1: '救助中', 2: '待确认', 3: '已完成', 4: '已关闭' };
                
                App.showModal('救助记录详情', `
                    <div class="form-group">
                        <label>记录编号</label>
                        <input type="text" value="${record.record_id}" disabled>
                    </div>
                    <div class="form-group">
                        <label>标题</label>
                        <input type="text" value="${record.title || '-'}" disabled>
                    </div>
                    <div class="form-group">
                        <label>上报人ID</label>
                        <input type="text" value="${record.user_id || '-'}" disabled>
                    </div>
                    <div class="form-group">
                        <label>接单志愿者ID</label>
                        <input type="text" value="${record.helper_id || '-'}" disabled>
                    </div>
                    <div class="form-group">
                        <label>关联动物ID</label>
                        <input type="text" value="${record.pet_id || '-'}" disabled>
                    </div>
                    <div class="form-group">
                        <label>动物名称</label>
                        <input type="text" value="${record.animal_name || '-'}" disabled>
                    </div>
                    <div class="form-group">
                        <label>发现位置</label>
                        <input type="text" value="${record.found_location_text || '-'}" disabled>
                    </div>
                    <div class="form-group">
                        <label>需求类型</label>
                        <input type="text" value="${record.need_type || '-'}" disabled>
                    </div>
                    <div class="form-group">
                        <label>情况说明</label>
                        <textarea disabled>${record.description || '-'}</textarea>
                    </div>
                    <div class="form-group">
                        <label>优先级</label>
                        <input type="text" value="${priorityMap[record.priority] || '普通'}" disabled>
                    </div>
                    <div class="form-group">
                        <label>状态</label>
                        <input type="text" value="${statusMap[record.status] || '未知'}" disabled>
                    </div>
                    <div class="form-group">
                        <label>创建时间</label>
                        <input type="text" value="${App.formatDateTime(record.created_at)}" disabled>
                    </div>
                    <div class="form-group">
                        <label>更新时间</label>
                        <input type="text" value="${App.formatDateTime(record.updated_at)}" disabled>
                    </div>
                    <div class="form-group">
                        <label>完成时间</label>
                        <input type="text" value="${App.formatDateTime(record.completed_at)}" disabled>
                    </div>
                `, [
                    { text: '关闭', class: 'btn-primary', onClick: () => App.hideModal() }
                ]);
            } else {
                App.showToast('获取详情失败', 'error');
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
