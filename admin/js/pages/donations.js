const DonationsPage = {
    currentPage: 1,
    pageSize: 20,
    donations: [],
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
            const result = await Api.admin.getDonations(this.currentPage, this.pageSize);
            
            if (result.success) {
                this.donations = result.data.donations || [];
                this.total = result.data.total || 0;
                content.innerHTML = this.renderContent();
            } else {
                content.innerHTML = `
                    <div class="card">
                        <div class="card-body">
                            ${App.showEmpty('⚠️', result.message || '获取捐款列表失败')}
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
        let filteredDonations = this.donations;
        if (this.statusFilter !== '') {
            filteredDonations = this.donations.filter(d => d.status === parseInt(this.statusFilter));
        }

        if (filteredDonations.length === 0 && this.donations.length === 0) {
            return `
                <div class="card">
                    <div class="card-body">
                        ${App.showEmpty('💰', '暂无捐款记录')}
                    </div>
                </div>
            `;
        }

        const totalPages = Math.ceil(this.total / this.pageSize);

        return `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">捐款记录列表</h3>
                    <span style="color: var(--text-light);">共 ${this.total} 条记录</span>
                </div>
                <div class="card-body">
                    <div class="filter-bar">
                        <select id="statusFilter" onchange="DonationsPage.filterByStatus()">
                            <option value="">全部状态</option>
                            <option value="0" ${this.statusFilter === '0' ? 'selected' : ''}>待确认</option>
                            <option value="1" ${this.statusFilter === '1' ? 'selected' : ''}>已到账</option>
                            <option value="2" ${this.statusFilter === '2' ? 'selected' : ''}>已驳回</option>
                            <option value="3" ${this.statusFilter === '3' ? 'selected' : ''}>已取消</option>
                        </select>
                    </div>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>捐款单号</th>
                                    <th>捐款人</th>
                                    <th>项目ID</th>
                                    <th>金额</th>
                                    <th>状态</th>
                                    <th>捐款时间</th>
                                    <th>审核人</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${filteredDonations.map(donation => this.renderRow(donation)).join('')}
                            </tbody>
                        </table>
                    </div>
                    ${totalPages > 1 ? this.renderPagination(totalPages) : ''}
                </div>
            </div>
        `;
    },

    renderRow(donation) {
        return `
            <tr>
                <td><span class="text-truncate" title="${donation.donation_id}">${donation.donation_id.substring(0, 10)}...</span></td>
                <td><span class="text-truncate" title="${donation.user_id}">${donation.user_id ? donation.user_id.substring(0, 8) + '...' : '-'}</span></td>
                <td>${donation.project_id || '-'}</td>
                <td style="color: var(--primary-color); font-weight: 600;">¥${parseFloat(donation.amount || 0).toFixed(2)}</td>
                <td>${App.formatStatus(donation.status, 'donation')}</td>
                <td>${App.formatDateTime(donation.created_at)}</td>
                <td>${donation.reviewed_by ? donation.reviewed_by.substring(0, 8) + '...' : '-'}</td>
                <td>
                    <div class="action-btns">
                        ${donation.status === 0 ? `
                            <button class="btn btn-sm btn-success" onclick="DonationsPage.approve('${donation.donation_id}')">
                                通过
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="DonationsPage.showReject('${donation.donation_id}')">
                                驳回
                            </button>
                        ` : `
                            <button class="btn btn-sm btn-warning" onclick="DonationsPage.showDetail('${donation.donation_id}')">
                                详情
                            </button>
                        `}
                    </div>
                </td>
            </tr>
        `;
    },

    renderPagination(totalPages) {
        let html = '<div class="pagination">';
        html += `<button ${this.currentPage <= 1 ? 'disabled' : ''} onclick="DonationsPage.goToPage(${this.currentPage - 1})">上一页</button>`;
        
        const startPage = Math.max(1, this.currentPage - 2);
        const endPage = Math.min(totalPages, this.currentPage + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            html += `<button class="${i === this.currentPage ? 'active' : ''}" onclick="DonationsPage.goToPage(${i})">${i}</button>`;
        }
        
        html += `<button ${this.currentPage >= totalPages ? 'disabled' : ''} onclick="DonationsPage.goToPage(${this.currentPage + 1})">下一页</button>`;
        html += '</div>';
        return html;
    },

    filterByStatus() {
        this.statusFilter = document.getElementById('statusFilter').value;
        const content = document.getElementById('pageContent');
        content.innerHTML = this.renderContent();
    },

    async approve(donationId) {
        if (!confirm('确认通过该捐款记录？')) return;
        
        try {
            const result = await Api.admin.approveDonation(donationId);
            
            if (result.success) {
                App.showToast('审核通过成功', 'success');
                this.loadData();
            } else {
                App.showToast(result.message || '操作失败', 'error');
            }
        } catch (error) {
            App.showToast('网络错误', 'error');
        }
    },

    showReject(donationId) {
        App.showModal('驳回捐款', `
            <div class="form-group">
                <label>捐款单号</label>
                <input type="text" value="${donationId}" disabled>
            </div>
            <div class="form-group">
                <label>驳回原因</label>
                <textarea id="rejectReason" placeholder="请输入驳回原因"></textarea>
            </div>
        `, [
            { text: '取消', class: 'btn-danger', onClick: () => App.hideModal() },
            { text: '确认驳回', class: 'btn-primary', onClick: () => this.reject(donationId) }
        ]);
    },

    async reject(donationId) {
        const reason = document.getElementById('rejectReason').value.trim();
        
        try {
            const result = await Api.admin.rejectDonation(donationId, reason);
            
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

    showDetail(donationId) {
        const donation = this.donations.find(d => d.donation_id === donationId);
        if (!donation) {
            App.showToast('未找到记录', 'error');
            return;
        }

        App.showModal('捐款详情', `
            <div class="form-group">
                <label>捐款单号</label>
                <input type="text" value="${donation.donation_id}" disabled>
            </div>
            <div class="form-group">
                <label>捐款人ID</label>
                <input type="text" value="${donation.user_id || '-'}" disabled>
            </div>
            <div class="form-group">
                <label>项目ID</label>
                <input type="text" value="${donation.project_id || '-'}" disabled>
            </div>
            <div class="form-group">
                <label>金额</label>
                <input type="text" value="¥${parseFloat(donation.amount || 0).toFixed(2)}" disabled>
            </div>
            <div class="form-group">
                <label>状态</label>
                <input type="text" value="${['待确认', '已到账', '已驳回', '已取消'][donation.status] || '未知'}" disabled>
            </div>
            <div class="form-group">
                <label>捐款时间</label>
                <input type="text" value="${App.formatDateTime(donation.created_at)}" disabled>
            </div>
            <div class="form-group">
                <label>审核人ID</label>
                <input type="text" value="${donation.reviewed_by || '-'}" disabled>
            </div>
            <div class="form-group">
                <label>审核时间</label>
                <input type="text" value="${App.formatDateTime(donation.reviewed_at)}" disabled>
            </div>
            <div class="form-group">
                <label>审核意见</label>
                <textarea disabled>${donation.review_comment || '-'}</textarea>
            </div>
        `, [
            { text: '关闭', class: 'btn-primary', onClick: () => App.hideModal() }
        ]);
    },

    async goToPage(page) {
        this.currentPage = page;
        await this.loadData();
    }
};
