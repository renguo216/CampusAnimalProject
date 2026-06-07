const AnimalsPage = {
    currentPage: 1,
    pageSize: 20,
    animals: [],
    total: 0,

    async render() {
        const content = document.getElementById('pageContent');
        content.innerHTML = App.showLoading();
        await this.loadData();
    },

    async loadData() {
        const content = document.getElementById('pageContent');
        
        try {
            const result = await Api.animal.getAll(this.currentPage, this.pageSize);
            
            if (result.success) {
                this.animals = result.data.animals || [];
                this.total = result.data.total || 0;
                content.innerHTML = this.renderContent();
            } else {
                content.innerHTML = `
                    <div class="card">
                        <div class="card-body">
                            ${App.showEmpty('⚠️', result.message || '获取动物列表失败')}
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
        if (this.animals.length === 0) {
            return `
                <div class="card">
                    <div class="card-body">
                        ${App.showEmpty('🐱', '暂无动物档案')}
                    </div>
                </div>
            `;
        }

        const totalPages = Math.ceil(this.total / this.pageSize);

        return `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">动物档案列表</h3>
                    <span style="color: var(--text-light);">共 ${this.total} 条记录</span>
                </div>
                <div class="card-body">
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>名字</th>
                                    <th>品种</th>
                                    <th>毛色</th>
                                    <th>年龄(月)</th>
                                    <th>性别</th>
                                    <th>绝育</th>
                                    <th>疫苗</th>
                                    <th>状态</th>
                                    <th>创建时间</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${this.animals.map(animal => this.renderRow(animal)).join('')}
                            </tbody>
                        </table>
                    </div>
                    ${totalPages > 1 ? this.renderPagination(totalPages) : ''}
                </div>
            </div>
        `;
    },

    renderRow(animal) {
        const genderMap = { 0: '未知', 1: '弟弟', 2: '妹妹' };
        const boolMap = { 0: '未知', 1: '是', 2: '否' };
        
        return `
            <tr>
                <td>${animal.pet_id}</td>
                <td>${animal.name || '-'}</td>
                <td>${animal.breed || '-'}</td>
                <td>${animal.color || '-'}</td>
                <td>${animal.age || 0}</td>
                <td>${genderMap[animal.gender] || '未知'}</td>
                <td>${boolMap[animal.is_neutered] || '未知'}</td>
                <td>${boolMap[animal.is_vaccinated] || '未知'}</td>
                <td>${App.formatStatus(animal.status, 'animal')}</td>
                <td>${App.formatDateTime(animal.created_at)}</td>
                <td>
                    <div class="action-btns">
                        <button class="btn btn-sm btn-primary" onclick="AnimalsPage.showEditStatus(${animal.pet_id}, ${animal.status})">
                            修改状态
                        </button>
                        <button class="btn btn-sm btn-warning" onclick="AnimalsPage.showDetail(${animal.pet_id})">
                            详情
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="AnimalsPage.showDeleteConfirm(${animal.pet_id}, '${animal.name}')">
                            删除
                        </button>
                    </div>
                </td>
            </tr>
        `;
    },

    renderPagination(totalPages) {
        let html = '<div class="pagination">';
        html += `<button ${this.currentPage <= 1 ? 'disabled' : ''} onclick="AnimalsPage.goToPage(${this.currentPage - 1})">上一页</button>`;
        
        const startPage = Math.max(1, this.currentPage - 2);
        const endPage = Math.min(totalPages, this.currentPage + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            html += `<button class="${i === this.currentPage ? 'active' : ''}" onclick="AnimalsPage.goToPage(${i})">${i}</button>`;
        }
        
        html += `<button ${this.currentPage >= totalPages ? 'disabled' : ''} onclick="AnimalsPage.goToPage(${this.currentPage + 1})">下一页</button>`;
        html += '</div>';
        return html;
    },

    showEditStatus(petId, currentStatus) {
        App.showModal('修改动物状态', `
            <div class="form-group">
                <label>动物ID</label>
                <input type="text" value="${petId}" disabled>
            </div>
            <div class="form-group">
                <label>新状态</label>
                <select id="newStatus">
                    <option value="0" ${currentStatus === 0 ? 'selected' : ''}>在校</option>
                    <option value="1" ${currentStatus === 1 ? 'selected' : ''}>已领养</option>
                    <option value="2" ${currentStatus === 2 ? 'selected' : ''}>需医疗</option>
                </select>
            </div>
        `, [
            { text: '取消', class: 'btn-danger', onClick: () => App.hideModal() },
            { text: '确认修改', class: 'btn-primary', onClick: () => this.updateStatus(petId) }
        ]);
    },

    async updateStatus(petId) {
        const newStatus = parseInt(document.getElementById('newStatus').value);
        
        try {
            const result = await Api.animal.updateStatus(petId, newStatus);
            
            if (result.success) {
                App.showToast('状态修改成功', 'success');
                App.hideModal();
                this.loadData();
            } else {
                App.showToast(result.message || '修改失败', 'error');
            }
        } catch (error) {
            App.showToast('网络错误', 'error');
        }
    },

    showDeleteConfirm(petId, name) {
        App.showModal('删除动物档案确认', `
            <div class="alert alert-danger">
                <p>确定要删除动物 <strong>${name || '编号' + petId}</strong> 的档案吗？</p>
                <p style="font-size: 0.9rem; margin-top: 0.5rem;">此操作不可逆！</p>
            </div>
        `, [
            { text: '取消', class: 'btn-primary', onClick: () => App.hideModal() },
            { text: '确认删除', class: 'btn-danger', onClick: () => this.deleteAnimal(petId) }
        ]);
    },

    async deleteAnimal(petId) {
        try {
            const result = await Api.animal.delete(petId);
            
            if (result.success) {
                App.showToast('动物档案已删除', 'success');
                App.hideModal();
                this.loadData();
            } else {
                App.showToast(result.message || '删除失败', 'error');
            }
        } catch (error) {
            App.showToast('网络错误', 'error');
        }
    },

    async showDetail(petId) {
        try {
            const result = await Api.animal.getById(petId);
            
            if (result.success && result.data) {
                const animal = result.data;
                const genderMap = { 0: '未知', 1: '弟弟', 2: '妹妹' };
                const boolMap = { 0: '未知', 1: '是', 2: '否' };
                
                App.showModal('动物详情', `
                    <div class="form-group">
                        <label>动物ID</label>
                        <input type="text" value="${animal.pet_id}" disabled>
                    </div>
                    <div class="form-group">
                        <label>名字</label>
                        <input type="text" value="${animal.name || '-'}" disabled>
                    </div>
                    <div class="form-group">
                        <label>品种</label>
                        <input type="text" value="${animal.breed || '-'}" disabled>
                    </div>
                    <div class="form-group">
                        <label>毛色</label>
                        <input type="text" value="${animal.color || '-'}" disabled>
                    </div>
                    <div class="form-group">
                        <label>年龄</label>
                        <input type="text" value="${animal.age || 0} 个月" disabled>
                    </div>
                    <div class="form-group">
                        <label>性别</label>
                        <input type="text" value="${genderMap[animal.gender] || '未知'}" disabled>
                    </div>
                    <div class="form-group">
                        <label>是否绝育</label>
                        <input type="text" value="${boolMap[animal.is_neutered] || '未知'}" disabled>
                    </div>
                    <div class="form-group">
                        <label>是否疫苗</label>
                        <input type="text" value="${boolMap[animal.is_vaccinated] || '未知'}" disabled>
                    </div>
                    <div class="form-group">
                        <label>性格描述</label>
                        <textarea disabled>${animal.personality || '-'}</textarea>
                    </div>
                    <div class="form-group">
                        <label>详细描述</label>
                        <textarea disabled>${animal.description || '-'}</textarea>
                    </div>
                    <div class="form-group">
                        <label>发现地点</label>
                        <input type="text" value="${animal.found_location || '-'}" disabled>
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
