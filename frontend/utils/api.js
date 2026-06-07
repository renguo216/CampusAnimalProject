const BASE_URL = 'http://192.168.143.73:5000/api/v1';

const request = (url, method, data = {}) => {
  const app = getApp();
  console.log('发送请求:', { url, method, data, baseURL: BASE_URL });
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
        console.log('请求成功:', res);
        if (res.statusCode === 200 || res.statusCode === 201) {
          resolve(res.data);
        } else {
          reject(res.data);
        }
      },
      fail: (err) => {
        console.error('请求失败:', err);
        reject(err);
      }
    });
  });
};

module.exports = {
  login: (code, userInfo) => {
    console.log('登录调用 - code:', code, 'userInfo:', userInfo);
    // 兼容不同的数据结构
    const userData = userInfo.userInfo || userInfo;
    return request('/user/login', 'POST', { 
      code, 
      userInfo: {
        user_id: code,  // 使用code作为临时user_id
        nickname: userData.nickName || userData.nickname, 
        avatar_url: userData.avatarUrl || userData.avatarURL 
      }
    });
  },
  getUser: (user_id) => request(`/user/${user_id}`, 'GET'),
  updateUserInfo: (data) => request('/user/update', 'POST', {
    nickname: data.nickname,
    avatarURL: data.avatarUrl || data.avatarURL,
    phone_number: data.phone_number
  }),
  uploadAvatar: (imageData) => request('/upload/avatar', 'POST', { image: imageData }),
  verifyStudent: (user_id, identity_no) => request('/user/verify', 'POST', { user_id, identity_no }),

  getPetList: (criteria) => request('/animals/search', 'GET', criteria),
  updatePetStatus: (pet_id, status) => request(`/animals/${pet_id}/status`, 'PUT', { status }),
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

  createRescueRecord: (recordData) => request('/rescue/records', 'POST', {
    title: recordData.title || '救助请求',
    location: recordData.location,
    found_location_text: recordData.found_location_text || recordData.location,
    description: recordData.description,
    need_type: recordData.need_type,
    photo_urls: recordData.photo_urls,
    animal_name: recordData.animal_name,
    status: recordData.status || 0,
    priority: recordData.priority || 0
  }),
  getRescueRecords: () => request('/rescue/records', 'GET'),
  getRescueRecordDetail: (record_id) => request(`/rescue/${record_id}`, 'GET'),
  claimRescue: (record_id) => request(`/rescue/${record_id}/claim`, 'POST'),
  completeRescue: (record_id) => request(`/rescue/${record_id}/complete`, 'POST'),
  confirmRescue: (record_id) => request(`/rescue/${record_id}/confirm`, 'POST'),
  closeRescue: (record_id) => request(`/rescue/${record_id}/close`, 'POST'),
  uploadRescuePhoto: (record_id, filePath) => {
    return new Promise((resolve, reject) => {
      wx.uploadFile({
        url: `${BASE_URL}/rescue/records/${record_id}/photo`,
        filePath: filePath,
        name: 'photo',
        success: (res) => resolve(JSON.parse(res.data)),
        fail: (err) => reject(err)
      });
    });
  },

  submitAdoption: (applyData) => request('/adoption/apply', 'POST', {
    pet_id: applyData.pet_id,
    content: applyData.content,
    phone_number: applyData.phone_number,
    housing_type: applyData.housing_type,
    experience: applyData.experience,
    occupation: applyData.occupation,
    contact_name: applyData.contact_name,
    status: 0
  }),
  getMyAdoptionRecords: () => request('/adoption/my-records', 'GET'),
  getAdoptionRecordDetail: (apply_id) => request(`/adoption/${apply_id}`, 'GET'),

  createDonationOrder: (donationData) => request('/donation/pay', 'POST', {
    user_id: donationData.user_id,
    project_id: donationData.project_id,
    amount: donationData.amount,
    status: 0
  }),
  getDonationRecords: (user_id) => request(`/donation/user/${user_id}`, 'GET'),
  getDonationProjects: () => request('/donation/projects', 'GET'),
  getDonationPublic: () => request('/donation/public', 'GET'),
  getHospitals: () => request('/hospitals', 'GET'),

  createPost: (postData) => request('/community/posts', 'POST', {
    content: postData.content,
    image_urls: postData.image_urls,
    status: 1
  }),
  getPosts: (page = 1) => request(`/community/posts?page=${page}`, 'GET'),
  likePost: (post_id) => request(`/community/posts/${post_id}/like`, 'POST'),
  deletePost: (post_id) => request(`/community/posts/${post_id}`, 'DELETE'),
  getPostDetail: (post_id) => request(`/community/posts/${post_id}`, 'GET'),
  getComments: (post_id) => request(`/comment?post_id=${post_id}`, 'GET'),
  commentPost: (post_id, content) => request(`/community/posts/${post_id}/comment`, 'POST', { content }),

  getVolunteerTasks: () => request('/tasks/volunteer', 'GET'),
  acceptTask: (task_id) => request(`/tasks/${task_id}/accept`, 'POST'),
  rejectTask: (task_id) => request(`/tasks/${task_id}/reject`, 'POST'),
  completeTask: (task_id, data) => request(`/tasks/${task_id}/complete`, 'POST', data),
  getTaskDetail: (task_id) => request(`/tasks/${task_id}`, 'GET'),

  applyVolunteer: (data) => request('/volunteer/apply', 'POST', {
    apply_content: data.apply_content || data.reason || data.content
  }),
  getVolunteerStatus: (user_id) => request(`/volunteer/user/${user_id}`, 'GET'),

  applyReimbursement: (data) => request('/reimbursement/apply', 'POST', {
    amount: data.amount,
    type: data.type,
    description: data.description,
    receipt_urls: data.receipt_urls,
    pet_id: data.pet_id,
    project_id: data.project_id,
    status: 0
  }),
  getMyReimbursements: () => request('/reimbursement/my-records', 'GET'),
  getReimbursementDetail: (reimb_id) => request(`/reimbursement/${reimb_id}`, 'GET'),

  getMyPoints: (user_id) => request('/points/my-points?user_id=' + user_id, 'GET'),
  getPointProducts: () => request('/points/products', 'GET'),
  exchangeProduct: (user_id, product_id) => request('/points/exchange', 'POST', { user_id, product_id }),
  getExchangeRecords: (user_id) => request('/points/exchange-records?user_id=' + user_id, 'GET'),
  getMyRescueRecords: (user_id) => request('/rescue/my-records?user_id=' + user_id, 'GET'),
  getMyAdoptionRecords: (user_id) => request('/adoption/my-records?user_id=' + user_id, 'GET'),
  getMyDonationHistory: (user_id) => request('/donation/history?user_id=' + user_id, 'GET'),

  getDashboardStats: () => request('/admin/dashboard/stats', 'GET'),
  getDonationTrend: () => request('/admin/dashboard/donation-trend', 'GET'),
  getVolunteerActivity: () => request('/admin/dashboard/volunteer-activity', 'GET'),
  getAdminExchangeRecords: () => request('/admin/points/exchange-records', 'GET'),
  
  // 新增的动物管理相关API
  addAnimal: (data) => request('/animals', 'POST', data),
  getAnimalListAll: (params) => request('/animals/search', 'GET', params),
  
  // 新增的图片上传API
  uploadAnimalImage: (filePath) => {
    return new Promise((resolve, reject) => {
      wx.uploadFile({
        url: `${BASE_URL}/upload/image`,
        filePath: filePath,
        name: 'image',
        success: (res) => {
          try {
            const data = JSON.parse(res.data);
            if (data.success && data.data && data.data.url) {
              resolve(data.data.url);
            } else {
              console.warn('图片上传失败:', data.message);
              resolve(null);
            }
          } catch (e) {
            console.error('解析上传响应失败:', e);
            resolve(null);
          }
        },
        fail: (err) => {
          console.error('上传图片失败:', err);
          resolve(null);
        }
      });
    });
  },
  
  // 新增的领养申请相关API - 适配后端接口
  createAdoptApplication: (data) => request('/adoption/apply', 'POST', {
    pet_id: data.petId,
    content: data.reason || data.content,
    contact_name: data.applicantName,
    phone_number: data.phone
  })
};
