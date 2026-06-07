const DashboardPage = {
    async render() {
        const content = document.getElementById('pageContent');
        content.innerHTML = App.showLoading();

        try {
            const result = await Api.admin.getStats();
            
            if (result.success) {
                const data = result.data;
                content.innerHTML = `
                    <div class="stats-grid">
                        <div class="stat-card clickable" onclick="DashboardPage.goToPage('users')">
                            <div class="stat-icon">👥</div>
                            <div class="stat-value">${data.users_count || 0}</div>
                            <div class="stat-label">用户总数</div>
                            <div class="stat-arrow">→</div>
                        </div>
                        <div class="stat-card clickable" onclick="DashboardPage.goToPage('animals')">
                            <div class="stat-icon">🐱</div>
                            <div class="stat-value">${data.animals_count || 0}</div>
                            <div class="stat-label">动物档案</div>
                            <div class="stat-arrow">→</div>
                        </div>
                        <div class="stat-card clickable" onclick="DashboardPage.goToPage('posts')">
                            <div class="stat-icon">📝</div>
                            <div class="stat-value">${data.posts_count || 0}</div>
                            <div class="stat-label">社区帖子</div>
                            <div class="stat-arrow">→</div>
                        </div>
                        <div class="stat-card clickable" onclick="DashboardPage.goToPage('donations')">
                            <div class="stat-icon">💰</div>
                            <div class="stat-value">${data.donations_count || 0}</div>
                            <div class="stat-label">捐款记录</div>
                            <div class="stat-arrow">→</div>
                        </div>
                        <div class="stat-card clickable" onclick="DashboardPage.goToPage('volunteers')">
                            <div class="stat-icon">🙋</div>
                            <div class="stat-value">${data.volunteers_count || 0}</div>
                            <div class="stat-label">志愿者申请</div>
                            <div class="stat-arrow">→</div>
                        </div>
                        <div class="stat-card clickable" onclick="DashboardPage.goToPage('adoptions')">
                            <div class="stat-icon">🏠</div>
                            <div class="stat-value">${data.adoptions_count || 0}</div>
                            <div class="stat-label">领养申请</div>
                            <div class="stat-arrow">→</div>
                        </div>
                        <div class="stat-card clickable" onclick="DashboardPage.goToPage('rescues')">
                            <div class="stat-icon">🚑</div>
                            <div class="stat-value">${data.rescues_count || 0}</div>
                            <div class="stat-label">救助记录</div>
                            <div class="stat-arrow">→</div>
                        </div>
                        <div class="stat-card clickable" onclick="DashboardPage.goToPage('products')">
                            <div class="stat-icon">🎁</div>
                            <div class="stat-value">${data.products_count || 0}</div>
                            <div class="stat-label">商品管理</div>
                            <div class="stat-arrow">→</div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">欢迎使用校园动物管理系统</h3>
                        </div>
                        <div class="card-body">
                            <p style="color: var(--text-light); line-height: 1.8;">
                                本系统为校园动物保护平台的管理后台，您可以在此进行以下操作：
                            </p>
                            <ul style="color: var(--text-light); line-height: 2; margin-top: 16px; padding-left: 20px;">
                                <li><strong>用户管理</strong>：查看所有用户信息，修改用户角色</li>
                                <li><strong>动物管理</strong>：查看动物档案，管理动物状态</li>
                                <li><strong>捐款管理</strong>：审核捐款记录，查看捐款详情</li>
                                <li><strong>志愿者管理</strong>：审核志愿者申请，管理志愿者信息</li>
                                <li><strong>领养管理</strong>：审核领养申请，查看领养记录</li>
                                <li><strong>救助管理</strong>：查看救助记录，跟踪救助进度</li>
                            </ul>
                            <div style="margin-top: 24px; padding: 16px; background: var(--primary-lighter); border-radius: 8px; border-left: 4px solid var(--primary-color);">
                                <p style="color: var(--text-color); font-weight: 500;">
                                    💡 提示：点击左侧菜单或上方统计卡片可快速跳转
                                </p>
                            </div>
                        </div>
                    </div>
                `;
            } else {
                content.innerHTML = `
                    <div class="card">
                        <div class="card-body">
                            ${App.showEmpty('⚠️', result.message || '获取统计数据失败')}
                        </div>
                    </div>
                `;
            }
        } catch (error) {
            content.innerHTML = `
                <div class="card">
                    <div class="card-body">
                        ${App.showEmpty('❌', '网络错误，请检查服务器连接')}
                    </div>
                </div>
            `;
        }
    },

    goToPage(page) {
        App.navigateTo(page);
    }
};
