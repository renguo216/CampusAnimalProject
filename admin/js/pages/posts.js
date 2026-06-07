const PostPage = {
    currentPage: 1,
    pageSize: 20,
    posts: [],
    total: 0,
    currentPostDetail: null,

    async render() {
        const content = document.getElementById('pageContent');
        content.innerHTML = App.showLoading();
        await this.loadData();
    },

    async loadData() {
        const content = document.getElementById('pageContent');
        
        try {
            const result = await Api.posts.getAll(this.currentPage, this.pageSize);
            
            if (result.success) {
                this.posts = result.data.posts || [];
                this.total = result.data.total || 0;
                content.innerHTML = this.renderContent();
            } else {
                content.innerHTML = `
                    <div class="card">
                        <div class="card-body">
                            ${App.showEmpty('⚠️', result.message || '获取帖子列表失败')}
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
                    <h3 class="card-title">帖子管理</h3>
                    <span style="color: var(--text-light);">共 ${this.total} 篇帖子</span>
                </div>
                <div class="card-body">
                    ${this.posts.length === 0 ? `
                        <div class="card-body">
                            ${App.showEmpty('📝', '暂无帖子')}
                        </div>
                    ` : `
                        <div class="table-container">
                            <table>
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>内容预览</th>
                                        <th>作者</th>
                                        <th>点赞数</th>
                                        <th>评论数</th>
                                        <th>状态</th>
                                        <th>创建时间</th>
                                        <th>操作</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${this.posts.map(post => this.renderRow(post)).join('')}
                                </tbody>
                            </table>
                        </div>
                        ${totalPages > 1 ? this.renderPagination(totalPages) : ''}
                    `}
                </div>
            </div>
        `;
    },

    renderRow(post) {
        const statusText = post.status === 1 ? '已发布' : '待审核';
        const statusClass = post.status === 1 ? 'status-active' : 'status-pending';
        const preview = post.content.length > 50 ? post.content.substring(0, 50) + '...' : post.content;

        return `
            <tr>
                <td>${post.post_id}</td>
                <td class="max-w-300">${preview || '<span style="color: #999;">无内容</span>'}</td>
                <td>
                    <div class="small-text">${post.user_nickname || '-'}</div>
                    <div class="text-xs text-gray">用户ID: ${post.user_id}</div>
                </td>
                <td><span class="points-badge">${post.like_count || 0}</span></td>
                <td><span class="points-badge">${post.comment_count || 0}</span></td>
                <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                <td>${App.formatDateTime(post.created_at)}</td>
                <td>
                    <div class="action-btns">
                        <button class="btn btn-sm btn-warning" onclick="PostPage.showDetail('${post.post_id}')">详情</button>
                        <button class="btn btn-sm btn-danger" onclick="PostPage.showDeleteConfirm('${post.post_id}')">删除</button>
                    </div>
                </td>
            </tr>
        `;
    },

    renderPagination(totalPages) {
        let html = '<div class="pagination">';
        html += `<button ${this.currentPage <= 1 ? 'disabled' : ''} onclick="PostPage.goToPage(${this.currentPage - 1})">上一页</button>`;
        
        const startPage = Math.max(1, this.currentPage - 2);
        const endPage = Math.min(totalPages, this.currentPage + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            html += `<button class="${i === this.currentPage ? 'active' : ''}" onclick="PostPage.goToPage(${i})">${i}</button>`;
        }
        
        html += `<button ${this.currentPage >= totalPages ? 'disabled' : ''} onclick="PostPage.goToPage(${this.currentPage + 1})">下一页</button>`;
        html += '</div>';
        return html;
    },

    async showDetail(postId) {
        const content = document.getElementById('pageContent');
        content.innerHTML = App.showLoading();
        
        try {
            const result = await Api.posts.getById(postId);
            
            if (result.success) {
                this.currentPostDetail = result.data;
                content.innerHTML = this.renderDetail();
            } else {
                content.innerHTML = `
                    <div class="card">
                        <div class="card-body">
                            ${App.showEmpty('⚠️', result.message || '获取帖子详情失败')}
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

    renderDetail() {
        const post = this.currentPostDetail;
        const statusText = post.status === 1 ? '已发布' : '待审核';
        const statusClass = post.status === 1 ? 'status-active' : 'status-pending';
        
        return `
            <div class="card">
                <div class="card-header">
                    <button class="btn btn-sm btn-secondary" onclick="PostPage.loadData()">← 返回列表</button>
                    <h3 class="card-title" style="margin-left: 1rem;">帖子详情</h3>
                </div>
                <div class="card-body">
                    <div class="post-detail">
                        <div class="post-meta">
                            <span class="label">作者：</span>
                            <span>${post.user_nickname || '-'}</span>
                            <span class="label" style="margin-left: 2rem;">状态：</span>
                            <span class="status-badge ${statusClass}">${statusText}</span>
                            <span class="label" style="margin-left: 2rem;">创建时间：</span>
                            <span>${App.formatDateTime(post.created_at)}</span>
                        </div>
                        
                        <div class="post-content">
                            <div class="label">内容：</div>
                            <p>${post.content || '无内容'}</p>
                        </div>
                        
                        ${post.image_urls ? `
                            <div class="post-images">
                                <div class="label">图片：</div>
                                <div class="image-grid">
                                    ${JSON.parse(post.image_urls).map((url, index) => `
                                        <img src="${url}" alt="图片${index + 1}" class="post-image">
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                        
                        <div class="post-stats">
                            <span class="stat-item">❤️ ${post.like_count || 0}</span>
                            <span class="stat-item">💬 ${post.comment_count || 0}</span>
                            <span class="stat-item">🔗 ${post.share_count || 0}</span>
                        </div>
                        
                        <div class="post-actions">
                            <button class="btn btn-danger" onclick="PostPage.showDeleteConfirm('${post.post_id}')">删除帖子</button>
                        </div>
                    </div>
                    
                    <div class="comments-section">
                        <h4 class="section-title">评论列表（${post.comments?.length || 0}）</h4>
                        ${post.comments && post.comments.length > 0 ? `
                            <div class="comments-list">
                                ${post.comments.map(comment => this.renderComment(comment)).join('')}
                            </div>
                        ` : `
                            <div class="empty-comments">暂无评论</div>
                        `}
                    </div>
                </div>
            </div>
        `;
    },

    renderComment(comment) {
        return `
            <div class="comment-item">
                <div class="comment-header">
                    <span class="comment-author">${comment.user_nickname || '-'}</span>
                    <span class="comment-time">${App.formatDateTime(comment.created_at)}</span>
                    <button class="btn btn-xs btn-danger" onclick="PostPage.showDeleteCommentConfirm('${comment.comment_id}', '${comment.user_nickname || '用户'}')">删除</button>
                </div>
                <div class="comment-content">${comment.content}</div>
                ${comment.like_count > 0 ? `<div class="comment-likes">❤️ ${comment.like_count}</div>` : ''}
            </div>
        `;
    },

    showDeleteConfirm(postId) {
        App.showModal('删除帖子确认', `
            <div class="alert alert-danger">
                <p>确定要删除这篇帖子吗？</p>
                <p style="font-size: 0.9rem; margin-top: 0.5rem;">此操作将同时删除该帖子下的所有评论，且不可逆！</p>
            </div>
        `, [
            { text: '取消', class: 'btn-primary', onClick: () => App.hideModal() },
            { text: '确认删除', class: 'btn-danger', onClick: () => this.deletePost(postId) }
        ]);
    },

    showDeleteCommentConfirm(commentId, nickname) {
        App.showModal('删除评论确认', `
            <div class="alert alert-danger">
                <p>确定要删除用户 <strong>${nickname}</strong> 的评论吗？</p>
                <p style="font-size: 0.9rem; margin-top: 0.5rem;">此操作不可逆！</p>
            </div>
        `, [
            { text: '取消', class: 'btn-primary', onClick: () => App.hideModal() },
            { text: '确认删除', class: 'btn-danger', onClick: () => this.deleteComment(commentId) }
        ]);
    },

    async deletePost(postId) {
        try {
            const result = await Api.posts.delete(postId);
            
            if (result.success) {
                App.showToast('帖子已删除', 'success');
                App.hideModal();
                this.loadData();
            } else {
                App.showToast(result.message || '删除失败', 'error');
            }
        } catch (error) {
            App.showToast('网络错误', 'error');
        }
    },

    async deleteComment(commentId) {
        try {
            const result = await Api.posts.deleteComment(commentId);
            
            if (result.success) {
                App.showToast('评论已删除', 'success');
                App.hideModal();
                if (this.currentPostDetail) {
                    await this.showDetail(this.currentPostDetail.post_id);
                }
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
