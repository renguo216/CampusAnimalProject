const API_BASE_URL = 'http://localhost:5000/api/v1';

const Api = {
    token: localStorage.getItem('admin_token') || '',

    setToken(token) {
        this.token = token;
        localStorage.setItem('admin_token', token);
    },

    clearToken() {
        this.token = '';
        localStorage.removeItem('admin_token');
    },

    async request(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        if (this.token) {
            defaultOptions.headers['Authorization'] = `Bearer ${this.token}`;
        }

        const finalOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers,
            },
        };

        try {
            const fullUrl = `${API_BASE_URL}${url}`;
            console.log('API请求:', finalOptions.method, fullUrl);
            console.log('请求体:', finalOptions.body);
            const response = await fetch(fullUrl, finalOptions);
            console.log('响应状态:', response.status);
            const data = await response.json();
            console.log('响应数据:', data);
            
            if (response.status === 401) {
                this.clearToken();
                window.location.reload();
            }
            
            return data;
        } catch (error) {
            console.error('API请求错误:', error);
            return { success: false, message: '网络请求失败，请检查服务器是否启动' };
        }
    },

    async get(url, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const fullUrl = queryString ? `${url}?${queryString}` : url;
        return this.request(fullUrl, { method: 'GET' });
    },

    async post(url, data = {}) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    async put(url, data = {}) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    },

    async del(url) {
        return this.request(url, { method: 'DELETE' });
    },

    async delete(url) {
        return this.request(url, { method: 'DELETE' });
    },

    admin: {
        getStats() {
            return Api.get('/admin/stats');
        },

        getUsers(page = 1, pageSize = 20) {
            return Api.get('/admin/users', { page, page_size: pageSize });
        },

        updateUserRole(userId, role) {
            return Api.put(`/admin/users/${userId}/role`, { role });
        },

        getAnimals(page = 1, pageSize = 20) {
            return Api.get('/admin/animals/all', { page, page_size: pageSize });
        },

        getDonations(page = 1, pageSize = 20) {
            return Api.get('/admin/donations/all', { page, page_size: pageSize });
        },

        approveDonation(donationId) {
            return Api.post(`/admin/donations/${donationId}/approve`);
        },

        rejectDonation(donationId, reason) {
            return Api.post(`/admin/donations/${donationId}/reject`, { reason });
        },

        getVolunteers(page = 1, pageSize = 20) {
            return Api.get('/admin/volunteers/all', { page, page_size: pageSize });
        },

        approveVolunteer(applicationId, reviewComment) {
            return Api.post(`/admin/volunteers/${applicationId}/approve`, { review_comment: reviewComment });
        },

        rejectVolunteer(applicationId, reason) {
            return Api.post(`/admin/volunteers/${applicationId}/reject`, { reason });
        },

        updateVolunteer(applicationId, status, reviewComment) {
            return Api.put(`/admin/volunteers/${applicationId}`, { status, review_comment: reviewComment });
        },

        getAdoptions(petId = null, page = 1, pageSize = 20) {
            const params = { page, page_size: pageSize };
            if (petId) params.pet_id = petId;
            return Api.get('/admin/adoptions/all', params);
        },

        getRescues(page = 1, pageSize = 20) {
            return Api.get('/admin/rescues/all', { page, page_size: pageSize });
        }
    },

    user: {
        login(userInfo) {
            return Api.post('/user/login', { userInfo });
        },

        getUser(userId) {
            return Api.get(`/user/${userId}`);
        },

        update(userId, data) {
            return Api.post('/user/update', { user_id: userId, ...data });
        },

        getAll(page = 1, pageSize = 20) {
            return Api.get('/admin/users', { page, page_size: pageSize });
        },

        updateRole(userId, role) {
            return Api.put(`/admin/users/${userId}/role`, { role });
        },

        delete(userId) {
            return Api.delete(`/admin/users/${userId}`);
        }
    },

    animal: {
        getAll(page = 1, pageSize = 20) {
            return Api.get('/animals/search', { page, page_size: pageSize });
        },

        getById(animalId) {
            return Api.get(`/animals/${animalId}`);
        },

        create(data) {
            return Api.post('/animals', data);
        },

        updateStatus(animalId, status) {
            return Api.put(`/animals/${animalId}/status`, { status });
        },

        delete(animalId) {
            return Api.delete(`/animals/${animalId}`);
        }
    },

    adoption: {
        approve(applyId, reviewComment) {
            return Api.post(`/adoption/${applyId}/approve`, { review_comment: reviewComment });
        },

        reject(applyId, reviewComment) {
            return Api.post(`/adoption/${applyId}/reject`, { review_comment: reviewComment });
        },

        update(applyId, status, reviewComment) {
            return Api.put(`/adoption/${applyId}`, { status, review_comment: reviewComment });
        },

        getAnimalApplications(petId, page = 1, pageSize = 20) {
            return Api.get(`/adoption/animal/${petId}`, { page, page_size: pageSize });
        }
    },

    volunteer: {
        approve(applicationId, reviewComment) {
            return Api.post(`/volunteer/${applicationId}/approve`, { review_comment: reviewComment });
        },

        reject(applicationId, reason) {
            return Api.post(`/volunteer/${applicationId}/reject`, { reason });
        }
    },

    rescue: {
        getAll(page = 1, pageSize = 20) {
            return Api.get('/rescue/records', { page, page_size: pageSize });
        },

        getById(recordId) {
            return Api.get(`/rescue/${recordId}`);
        }
    },

    donation: {
        getAll(page = 1, pageSize = 20) {
            return Api.get('/donation', { page, page_size: pageSize });
        }
    },

    donationProject: {
        getAll(page = 1, pageSize = 20) {
            return Api.get('/donation/projects', { page, page_size: pageSize });
        }
    },

    product: {
        getAll(page = 1, pageSize = 20) {
            return Api.get('/points/products/all', { page, page_size: pageSize });
        },

        getById(productId) {
            return Api.get(`/points/${productId}`);
        },

        create(data) {
            return Api.post('/points', data);
        },

        update(productId, data) {
            return Api.put(`/points/${productId}`, data);
        },

        updateStatus(productId, status) {
            return Api.put(`/points/${productId}/status`, { status });
        },

        updateStock(productId, stock) {
            return Api.put(`/points/${productId}/stock`, { stock });
        },

        delete(productId) {
            return Api.delete(`/points/${productId}`);
        }
    },

    posts: {
        getAll(page = 1, pageSize = 20) {
            return Api.get('/community/posts', { page, page_size: pageSize });  
        },

        getById(postId) {
            return Api.get(`/community/posts/${postId}`);
        },

        delete(postId) {
            return Api.delete(`/community/posts/${postId}/admin`);
        },

        deleteComment(commentId) {
            return Api.delete(`/comment/admin/${commentId}`);
        }
    }
};
