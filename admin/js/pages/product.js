const ProductPage = {
    currentPage: 1,
    pageSize: 20,
    products: [],
    total: 0,

    async render() {
        const content = document.getElementById('pageContent');
        content.innerHTML = App.showLoading();
        await this.loadData();
    },

    async loadData() {
        const content = document.getElementById('pageContent');
        
        try {
            const result = await Api.product.getAll(this.currentPage, this.pageSize);
            
            if (result.success) {
                this.products = result.data.products || [];
                this.total = result.data.total || 0;
                content.innerHTML = this.renderContent();
            } else {
                content.innerHTML = `
                    <div class="card">
                        <div class="card-body">
                            ${App.showEmpty('⚠️', result.message || '获取商品列表失败')}
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
        const totalPages = Math.ceil(this.total / this.pageSize);

        return `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">积分商品管理</h3>
                    <span style="color: var(--text-light);">共 ${this.total} 个商品</span>
                    <button class="btn btn-primary" onclick="ProductPage.showAddModal()">
                        + 添加商品
                    </button>
                </div>
                <div class="card-body">
                    ${this.products.length === 0 ? `
                        <div class="card-body">
                            ${App.showEmpty('🎁', '暂无积分商品')}
                        </div>
                    ` : `
                        <div class="table-container">
                            <table>
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>商品名称</th>
                                        <th>所需积分</th>
                                        <th>库存</th>
                                        <th>状态</th>
                                        <th>创建时间</th>
                                        <th>操作</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${this.products.map(product => this.renderRow(product)).join('')}
                                </tbody>
                            </table>
                        </div>
                        ${totalPages > 1 ? this.renderPagination(totalPages) : ''}
                    `}
                </div>
            </div>
        `;
    },

    renderRow(product) {
        const statusText = product.status === 1 ? '上架' : '下架';
        const statusClass = product.status === 1 ? 'status-active' : 'status-inactive';
        
        return `
            <tr>
                <td>${product.product_id}</td>
                <td>${product.name || '-'}</td>
                <td><span class="points-badge">${product.points_required || 0}</span></td>
                <td>${product.stock || 0}</td>
                <td>
                    <span class="status-badge ${statusClass}">${statusText}</span>
                </td>
                <td>${App.formatDateTime(product.created_at)}</td>
                <td>
                    <div class="action-btns">
                        <button class="btn btn-sm btn-primary" onclick="ProductPage.showEditModal(${product.product_id})">
                            编辑
                        </button>
                        <button class="btn btn-sm btn-warning" onclick="ProductPage.toggleStatus(${product.product_id}, ${product.status})">
                            ${product.status === 1 ? '下架' : '上架'}
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="ProductPage.showDeleteConfirm(${product.product_id}, '${product.name}')">
                            删除
                        </button>
                    </div>
                </td>
            </tr>
        `;
    },

    renderPagination(totalPages) {
        let html = '<div class="pagination">';
        html += `<button ${this.currentPage <= 1 ? 'disabled' : ''} onclick="ProductPage.goToPage(${this.currentPage - 1})">上一页</button>`;
        
        const startPage = Math.max(1, this.currentPage - 2);
        const endPage = Math.min(totalPages, this.currentPage + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            html += `<button class="${i === this.currentPage ? 'active' : ''}" onclick="ProductPage.goToPage(${i})">${i}</button>`;
        }
        
        html += `<button ${this.currentPage >= totalPages ? 'disabled' : ''} onclick="ProductPage.goToPage(${this.currentPage + 1})">下一页</button>`;
        html += '</div>';
        return html;
    },

    showAddModal() {
        App.showModal('添加积分商品', `
            <div class="form-group">
                <label>商品名称 *</label>
                <input type="text" id="addName" placeholder="请输入商品名称">
            </div>
            <div class="form-group">
                <label>所需积分 *</label>
                <input type="number" id="addPoints" placeholder="请输入所需积分" min="0">
            </div>
            <div class="form-group">
                <label>库存</label>
                <input type="number" id="addStock" placeholder="请输入库存数量" min="0" value="0">
            </div>
            <div class="form-group">
                <label>商品描述</label>
                <textarea id="addDescription" placeholder="请输入商品描述"></textarea>
            </div>
            <div class="form-group">
                <label>商品图片URL</label>
                <input type="text" id="addImageUrl" placeholder="请输入商品图片URL">
            </div>
            <div class="form-group">
                <label>状态</label>
                <select id="addStatus">
                    <option value="1" selected>上架</option>
                    <option value="0">下架</option>
                </select>
            </div>
        `, [
            { text: '取消', class: 'btn-danger', onClick: () => App.hideModal() },
            { text: '确认添加', class: 'btn-primary', onClick: () => this.addProduct() }
        ]);
    },

    async addProduct() {
        const name = document.getElementById('addName').value;
        const pointsRequired = parseInt(document.getElementById('addPoints').value);
        const stock = parseInt(document.getElementById('addStock').value) || 0;
        const description = document.getElementById('addDescription').value;
        const imageUrl = document.getElementById('addImageUrl').value;
        const status = parseInt(document.getElementById('addStatus').value);

        if (!name || isNaN(pointsRequired) || pointsRequired < 0) {
            App.showToast('请填写正确的商品名称和积分', 'error');
            return;
        }

        try {
            const result = await Api.product.create({
                name,
                points_required: pointsRequired,
                stock,
                description,
                image_url: imageUrl,
                status
            });
            
            if (result.success) {
                App.showToast('商品添加成功', 'success');
                App.hideModal();
                this.loadData();
            } else {
                App.showToast(result.message || '添加失败', 'error');
            }
        } catch (error) {
            App.showToast('网络错误', 'error');
        }
    },

    async showEditModal(productId) {
        try {
            const result = await Api.product.getById(productId);
            
            if (result.success && result.data) {
                const product = result.data;
                
                App.showModal('编辑商品信息', `
                    <div class="form-group">
                        <label>商品ID</label>
                        <input type="text" value="${product.product_id}" disabled>
                    </div>
                    <div class="form-group">
                        <label>商品名称 *</label>
                        <input type="text" id="editName" value="${product.name || ''}">
                    </div>
                    <div class="form-group">
                        <label>所需积分 *</label>
                        <input type="number" id="editPoints" value="${product.points_required || 0}" min="0">
                    </div>
                    <div class="form-group">
                        <label>库存</label>
                        <input type="number" id="editStock" value="${product.stock || 0}" min="0">
                    </div>
                    <div class="form-group">
                        <label>商品描述</label>
                        <textarea id="editDescription">${product.description || ''}</textarea>
                    </div>
                    <div class="form-group">
                        <label>商品图片URL</label>
                        <input type="text" id="editImageUrl" value="${product.image_url || ''}">
                    </div>
                    <div class="form-group">
                        <label>状态</label>
                        <select id="editStatus">
                            <option value="1" ${(product.status || 1) === 1 ? 'selected' : ''}>上架</option>
                            <option value="0" ${product.status === 0 ? 'selected' : ''}>下架</option>
                        </select>
                    </div>
                `, [
                    { text: '取消', class: 'btn-danger', onClick: () => App.hideModal() },
                    { text: '确认修改', class: 'btn-primary', onClick: () => this.updateProduct(productId) }
                ]);
            } else {
                App.showToast('获取商品信息失败', 'error');
            }
        } catch (error) {
            App.showToast('网络错误', 'error');
        }
    },

    async updateProduct(productId) {
        const name = document.getElementById('editName').value;
        const pointsRequired = parseInt(document.getElementById('editPoints').value);
        const stock = parseInt(document.getElementById('editStock').value) || 0;
        const description = document.getElementById('editDescription').value;
        const imageUrl = document.getElementById('editImageUrl').value;
        const status = parseInt(document.getElementById('editStatus').value);

        if (!name || isNaN(pointsRequired) || pointsRequired < 0) {
            App.showToast('请填写正确的商品名称和积分', 'error');
            return;
        }

        try {
            const result = await Api.product.update(productId, {
                name,
                points_required: pointsRequired,
                stock,
                description,
                image_url: imageUrl,
                status
            });
            
            if (result.success) {
                App.showToast('商品信息更新成功', 'success');
                App.hideModal();
                this.loadData();
            } else {
                App.showToast(result.message || '更新失败', 'error');
            }
        } catch (error) {
            App.showToast('网络错误', 'error');
        }
    },

    async toggleStatus(productId, currentStatus) {
        const newStatus = currentStatus === 1 ? 0 : 1;
        const statusText = newStatus === 1 ? '上架' : '下架';

        try {
            const result = await Api.product.updateStatus(productId, newStatus);
            
            if (result.success) {
                App.showToast(`商品已${statusText}`, 'success');
                this.loadData();
            } else {
                App.showToast(result.message || `${statusText}失败`, 'error');
            }
        } catch (error) {
            App.showToast('网络错误', 'error');
        }
    },

    showDeleteConfirm(productId, name) {
        App.showModal('删除商品确认', `
            <div class="alert alert-danger">
                <p>确定要删除商品 <strong>${name || '编号' + productId}</strong> 吗？</p>
                <p style="font-size: 0.9rem; margin-top: 0.5rem;">此操作不可逆！</p>
            </div>
        `, [
            { text: '取消', class: 'btn-primary', onClick: () => App.hideModal() },
            { text: '确认删除', class: 'btn-danger', onClick: () => this.deleteProduct(productId) }
        ]);
    },

    async deleteProduct(productId) {
        try {
            const result = await Api.product.delete(productId);
            
            if (result.success) {
                App.showToast('商品已删除', 'success');
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
