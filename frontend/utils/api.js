const BASE_URL = 'http://192.168.8.73:3000/api/v1';

const request = (url, method, data = {}) => {
  const app = getApp();
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${BASE_URL}${url}`,
      method: method,
      data: data,
      header: {
        'Content-Type': 'application/json',
        'Authorization': app.globalData.token ? `Bearer ${app.globalData.token}` : ''
      },
      success: (res) => {
        if (res.statusCode === 200 || res.statusCode === 201) {
          resolve(res.data);
        } else {
          reject(res.data);
        }
      },
      fail: (err) => reject(err)
    });
  });
};

module.exports = {
  login: (code, userInfo) => request('/user/login', 'POST', { code, ...userInfo }),
  updateUserInfo: (data) => request('/user/update', 'POST', data),
  uploadAvatar: (imageData) => request('/upload/avatar', 'POST', { image: imageData }),
  verifyStudent: (userId, identityNo) => request('/user/verify', 'POST', { userId, identityNo }),

  getPetList: (criteria) => request('/animals/search', 'GET', criteria),
  updatePetStatus: (petId, status) => request(`/animals/${petId}/status`, 'PUT', { status }),
  aiIdentify: (filePath) => {
    return new Promise((resolve, reject) => {
      wx.uploadFile({
        url: `${BASE_URL}/ai/recognize`,
        filePath: filePath,
        name: 'photo',
        success: (res) => resolve(JSON.parse(res.data)),
        fail: (err) => reject(err)
      });
    });
  },

  createRescueRecord: (recordData) => request('/rescue/records', 'POST', recordData),
  getMyRescueRecords: () => request('/rescue/my-records', 'GET'),
  getRescueRecordDetail: (id) => request(`/rescue/records/${id}`, 'GET'),
  uploadRescuePhoto: (id, filePath) => {
    return new Promise((resolve, reject) => {
      wx.uploadFile({
        url: `${BASE_URL}/rescue/records/${id}/photo`,
        filePath: filePath,
        name: 'photo',
        success: (res) => resolve(JSON.parse(res.data)),
        fail: (err) => reject(err)
      });
    });
  },

  submitAdoption: (applyData) => request('/adoption/apply', 'POST', applyData),
  getMyAdoptionRecords: () => request('/adoption/my-records', 'GET'),
  getAdoptionRecordDetail: (id) => request(`/adoption/apply/${id}`, 'GET'),

  createDonationOrder: (donationData) => request('/donation/pay', 'POST', donationData),
  getDonationRecords: () => request('/donation/my-records', 'GET'),
  getDonationProjects: () => request('/donation/projects', 'GET'),
  getDonationPublic: () => request('/donation/public', 'GET'),

  createPost: (postContent) => request('/community/posts', 'POST', postContent),
  getPosts: (type) => request('/community/posts', 'GET', { type }),
  likePost: (postId, change) => request(`/community/posts/${postId}/like`, 'PUT', { change }),
  deletePost: (postId) => request(`/community/posts/${postId}`, 'DELETE'),

  getVolunteerTasks: () => request('/tasks/volunteer', 'GET'),
  acceptTask: (taskId) => request(`/tasks/${taskId}/accept`, 'POST'),
  rejectTask: (taskId) => request(`/tasks/${taskId}/reject`, 'POST'),
  completeTask: (taskId, data) => request(`/tasks/${taskId}/complete`, 'POST', data),
  getTaskDetail: (taskId) => request(`/tasks/${taskId}`, 'GET'),

  applyVolunteer: (data) => request('/volunteer/apply', 'POST', data),
  getVolunteerStatus: () => request('/volunteer/status', 'GET'),

  applyReimbursement: (data) => request('/reimbursement/apply', 'POST', data),
  getMyReimbursements: () => request('/reimbursement/my-records', 'GET'),
  getReimbursementDetail: (id) => request(`/reimbursement/${id}`, 'GET'),

  getMyPoints: () => request('/points/my-points', 'GET'),
  getPointProducts: () => request('/points/products', 'GET'),
  exchangeProduct: (productId) => request('/points/exchange', 'POST', { productId }),
  getExchangeRecords: () => request('/points/exchange-records', 'GET'),

  getDashboardStats: () => request('/admin/dashboard/stats', 'GET'),
  getDonationTrend: () => request('/admin/dashboard/donation-trend', 'GET'),
  getVolunteerActivity: () => request('/admin/dashboard/volunteer-activity', 'GET'),

  getUserList: () => request('/admin/users', 'GET'),
  updateUserRole: (userId, role) => request(`/admin/users/${userId}/role`, 'PUT', { role }),
  getVolunteerApplications: () => request('/admin/volunteer-applications', 'GET'),
  reviewVolunteerApplication: (userId, status) => request(`/admin/volunteer-applications/${userId}/review`, 'POST', { status }),

  getAllRescueRecords: () => request('/admin/rescue-records', 'GET'),
  updateRescueStatus: (id, status) => request(`/admin/rescue-records/${id}/status`, 'PUT', { status }),

  getAllAnimals: () => request('/admin/animals', 'GET'),
  addAnimal: (data) => request('/admin/animals', 'POST', data),
  updateAnimal: (id, data) => request(`/admin/animals/${id}`, 'PUT', data),
  getAdoptionApplications: () => request('/admin/adoption-applications', 'GET'),
  reviewAdoptionApplication: (id, status) => request(`/admin/adoption-applications/${id}/review`, 'POST', { status }),
  addFollowUp: (adoptionId, data) => request(`/admin/adoption/${adoptionId}/follow-up`, 'POST', data),

  manageDonationPublic: (data) => request('/admin/donation/public', 'POST', data),
  reviewReimbursement: (id, status) => request(`/admin/reimbursement/${id}/review`, 'POST', { status }),
  getFinancialRecords: () => request('/admin/financial/records', 'GET'),

  getPendingPosts: () => request('/admin/community/pending-posts', 'GET'),
  approvePost: (postId) => request(`/admin/community/posts/${postId}/approve`, 'POST'),
  deleteComment: (commentId) => request(`/admin/community/comments/${commentId}`, 'DELETE'),

  getAllProducts: () => request('/admin/products', 'GET'),
  addProduct: (data) => request('/admin/products', 'POST', data),
  updateProduct: (id, data) => request(`/admin/products/${id}`, 'PUT', data),
  getAllExchangeRecords: () => request('/admin/points/exchange-records', 'GET'),

  getRolePermissions: (role) => request('/admin/permissions', 'GET', { role }),
  updateRolePermissions: (role, permissions) => request('/admin/permissions', 'PUT', { role, permissions }),
  getAuditLogs: () => request('/admin/audit/logs', 'GET'),
  updateSystemConfig: (config) => request('/admin/config', 'PUT', config)
};