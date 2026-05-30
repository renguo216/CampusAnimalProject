const http = require('http');
const url = require('url');
const fs = require('fs');
const path = require('path');

const PORT = 3000;
const HOST = '0.0.0.0';

const USER_DATA_FILE = path.join(__dirname, 'user_data.json');
const UPLOADS_DIR = path.join(__dirname, 'uploads');

if (!fs.existsSync(UPLOADS_DIR)) {
  fs.mkdirSync(UPLOADS_DIR, { recursive: true });
}

function loadUserDatabase() {
  try {
    if (fs.existsSync(USER_DATA_FILE)) {
      const data = fs.readFileSync(USER_DATA_FILE, 'utf8');
      return JSON.parse(data);
    }
  } catch (err) {
    console.error('加载用户数据失败:', err);
  }
  return {};
}

function saveUserDatabase() {
  try {
    fs.writeFileSync(USER_DATA_FILE, JSON.stringify(userDatabase, null, 2));
  } catch (err) {
    console.error('保存用户数据失败:', err);
  }
}

const mockUsers = [
  {
    user_id: 'u001',
    nickname: '爱心志愿者',
    avatarURL: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20cartoon%20cat%20avatar%20friendly&image_size=square',
    role: 2,
    points: 150,
    phone_number: '13800138001',
    like_count: 0,
    follower_count: 0,
    following_count: 0,
    is_active: 1,
    created_at: '2024-01-01'
  },
  {
    user_id: 'u002',
    nickname: '校园铲屎官',
    avatarURL: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20cartoon%20dog%20avatar%20happy&image_size=square',
    role: 1,
    points: 0,
    phone_number: '',
    like_count: 0,
    follower_count: 0,
    following_count: 0,
    is_active: 1,
    created_at: '2024-01-02'
  },
  {
    user_id: 'u003',
    nickname: '管理员小王',
    avatarURL: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=professional%20admin%20avatar%20friendly&image_size=square',
    role: 3,
    points: 0,
    phone_number: '13800138003',
    like_count: 0,
    follower_count: 0,
    following_count: 0,
    is_active: 1,
    created_at: '2024-01-03'
  }
];

const verifyCodeStore = {};

let userDatabase = loadUserDatabase();

const mockAnimals = [
  {
    id: 'a001',
    name: '橘猫',
    type: 'cat',
    color: '橘色',
    status: 'stray',
    location: '图书馆附近',
    description: '非常亲人的橘猫，喜欢蹭人',
    image: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=orange%20tabby%20cat%20cute%20friendly&image_size=portrait_4_3',
    createTime: '2024-01-15'
  },
  {
    id: 'a002',
    name: '小黑',
    type: 'dog',
    color: '黑色',
    status: 'rescue',
    location: '食堂门口',
    description: '流浪小狗，性格温顺',
    image: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=black%20puppy%20cute%20friendly&image_size=portrait_4_3',
    createTime: '2024-01-20'
  },
  {
    id: 'a003',
    name: '花花',
    type: 'cat',
    color: '三花',
    status: 'adopt',
    location: '宠物救助站',
    description: '三花猫，已完成疫苗接种',
    image: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=calico%20cat%20beautiful%20fluffy&image_size=portrait_4_3',
    createTime: '2024-02-01'
  }
];

const mockVolunteerTasks = [
  {
    id: 1,
    type: 'rescue',
    typeText: '动物救助',
    status: 'pending',
    statusText: '待接单',
    title: '图书馆门口受伤猫咪',
    location: '西科大图书馆',
    time: '10分钟前',
    description: '发现一只橘猫后腿受伤，无法行走，需要紧急救助',
    image: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=injured%20orange%20cat%20sad&image_size=square',
    latitude: 39.908823,
    longitude: 116.397470
  },
  {
    id: 2,
    type: 'medical',
    typeText: '医疗协助',
    status: 'pending',
    statusText: '待接单',
    title: '需要协助送医',
    location: '学生宿舍区',
    time: '30分钟前',
    description: '有一只狗狗需要送到宠物医院，请志愿者协助',
    image: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20dog%20sad%20need%20help&image_size=square',
    latitude: 39.909823,
    longitude: 116.398470
  }
];

const mockDonationProjects = [
  {
    id: 1,
    title: '流浪猫医疗救助基金',
    description: '为受伤流浪猫提供医疗费用',
    targetAmount: 5000,
    currentAmount: 3200,
    participantCount: 156
  },
  {
    id: 2,
    title: '食物补给计划',
    description: '为校园流浪动物提供食物',
    targetAmount: 2000,
    currentAmount: 1500,
    participantCount: 89
  },
  {
    id: 3,
    title: '绝育手术基金',
    description: '支持TNR绝育计划',
    targetAmount: 3000,
    currentAmount: 2100,
    participantCount: 120
  }
];

const mockCommunityPosts = [
  {
    id: 1,
    author: '爱心志愿者',
    avatar: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20cat%20avatar&image_size=square',
    content: '今天在图书馆门口发现了一只受伤的小橘猫，已经送往宠物医院治疗了。希望大家多多关注校园流浪动物！',
    images: ['https://neeko-copilot.bytedance.net/api/text_to_image?prompt=orange%20cat%20hospital&image_size=square'],
    likes: 45,
    comments: 12,
    shares: 5,
    createTime: '2小时前'
  },
  {
    id: 2,
    author: '校园铲屎官',
    avatar: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cute%20dog%20avatar&image_size=square',
    content: '领养代替购买，给流浪动物一个温暖的家。我家的小黑现在已经是我最好的朋友啦~',
    images: ['https://neeko-copilot.bytedance.net/api/text_to_image?prompt=happy%20dog%20with%20owner&image_size=square'],
    likes: 89,
    comments: 23,
    shares: 15,
    createTime: '5小时前'
  }
];

function generateToken(userId) {
  return 'token_' + userId + '_' + Date.now();
}

function sendResponse(res, statusCode, data) {
  res.writeHead(statusCode, {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
  });
  res.end(JSON.stringify(data));
}

function parseBody(req) {
  return new Promise((resolve) => {
    let body = '';
    req.on('data', (chunk) => {
      body += chunk.toString();
    });
    req.on('end', () => {
      try {
        resolve(JSON.parse(body));
      } catch {
        resolve({});
      }
    });
  });
}

const server = http.createServer(async (req, res) => {
  const parsedUrl = url.parse(req.url, true);
  const pathname = parsedUrl.pathname;
  const method = req.method;

  console.log(`[${new Date().toLocaleString()}] ${method} ${pathname}`);

  if (method === 'OPTIONS') {
    console.log('处理 OPTIONS 请求');
    sendResponse(res, 200, {});
    return;
  }

  if (method === 'POST' && pathname === '/api/v1/user/login') {
    const body = await parseBody(req);
    console.log('登录请求 body:', JSON.stringify(body));
    const { code } = body;
    
    if (!code || code === 'test') {
      console.log('使用模拟用户登录');
    }

    let userData = body.userInfo || {};
    let rawData = body.rawData ? JSON.parse(body.rawData) : null;
    let userId = 'user_' + Date.now();
    const token = generateToken(userId);
    
    let userIdentifier = '';
    if (rawData) {
      userIdentifier = `${rawData.nickName || ''}_${rawData.avatarUrl || ''}_${rawData.city || ''}`;
    } else {
      userIdentifier = JSON.stringify(userData);
    }
    
    console.log('用户标识:', userIdentifier);
    
    let existingUserId = null;
    
    const oldUsers = Object.keys(userDatabase).filter(uid => !userDatabase[uid].userIdentifier);
    console.log('旧用户列表:', oldUsers);
    
    if (oldUsers.length > 0) {
      existingUserId = oldUsers.find(uid => {
        const user = userDatabase[uid];
        return user.avatarURL && user.avatarURL.includes('thirdwx.qlogo.cn');
      });
      
      if (existingUserId) {
        console.log(`找到旧用户: ${existingUserId}`);
      }
    }
    
    if (!existingUserId) {
      existingUserId = Object.keys(userDatabase).find(
        uid => userDatabase[uid].userIdentifier === userIdentifier
      );
      
      if (existingUserId) {
        console.log(`按userIdentifier找到用户: ${existingUserId}`);
      }
    }
    
    if (!existingUserId && userData.avatarUrl) {
      existingUserId = Object.keys(userDatabase).find(
        uid => userDatabase[uid].avatarURL === userData.avatarUrl
      );
      
      if (existingUserId) {
        console.log(`按头像URL找到用户: ${existingUserId}`);
      }
    }
    
    if (existingUserId) {
      userId = existingUserId;
      console.log(`找到已有用户: ${userId}`);
      
      userDatabase[userId] = {
        ...userDatabase[userId],
        userIdentifier: userIdentifier
      };
      saveUserDatabase();
    } else {
      userDatabase[userId] = {
        user_id: userId,
        userIdentifier: userIdentifier,
        nickname: userData.nickName || '爱心志愿者',
        avatarURL: userData.avatarUrl || '',
        role: 1,
        points: 0,
        phone_number: '',
        volunteer_id: null,
        admin_id: null,
        level: 1,
        like_count: 0,
        follower_count: 0,
        following_count: 0,
        is_active: 1,
        created_at: new Date().toISOString().split('T')[0]
      };
      console.log(`新用户注册并登录: ${userId} - ${userData.nickName}`);
      saveUserDatabase();
    }
    
    const currentUser = userDatabase[userId];
    
    console.log(`微信登录成功: ${userId}`);
    sendResponse(res, 200, {
      success: true,
      token,
      user: {
        user_id: currentUser.user_id,
        nickname: currentUser.nickname,
        avatarURL: currentUser.avatarURL,
        role: currentUser.role,
        points: currentUser.points || 0,
        phone_number: currentUser.phone_number || '',
        level: currentUser.level || 1
      }
    });
    return;
  }

  if (method === 'POST' && pathname === '/api/v1/upload/avatar') {
    const body = await parseBody(req);
    const authHeader = req.headers['authorization'];
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      sendResponse(res, 401, { success: false, message: '未授权' });
      return;
    }
    
    const token = authHeader.split(' ')[1];
    const tokenParts = token.split('_');
    let userId = tokenParts[2] ? 'user_' + tokenParts[2] : null;
    
    if (!userId || !userDatabase[userId]) {
      userId = Object.keys(userDatabase)[0] || 'user_' + Date.now();
    }
    
    if (!body.image) {
      sendResponse(res, 400, { success: false, message: '缺少图片数据' });
      return;
    }
    
    try {
      const base64Data = body.image.replace(/^data:image\/\w+;base64,/, '');
      const imageBuffer = Buffer.from(base64Data, 'base64');
      const filename = `${userId}_${Date.now()}.jpg`;
      const filepath = path.join(UPLOADS_DIR, filename);
      
      fs.writeFileSync(filepath, imageBuffer);
      
      const avatarUrl = `http://192.168.8.73:3000/uploads/${filename}`;
      
      userDatabase[userId].avatarURL = avatarUrl;
      saveUserDatabase();
      
      console.log(`头像上传成功: ${userId} -> ${avatarUrl}`);
      
      sendResponse(res, 200, {
        success: true,
        message: '头像上传成功',
        avatarUrl: avatarUrl
      });
    } catch (err) {
      console.error('头像上传失败:', err);
      sendResponse(res, 500, { success: false, message: '头像上传失败' });
    }
    return;
  }

  if (method === 'GET' && pathname.startsWith('/uploads/')) {
    const filename = pathname.replace('/uploads/', '');
    const filepath = path.join(UPLOADS_DIR, filename);
    
    if (!fs.existsSync(filepath)) {
      res.writeHead(404);
      res.end('File not found');
      return;
    }
    
    const fileContent = fs.readFileSync(filepath);
    res.writeHead(200, {
      'Content-Type': 'image/jpeg',
      'Access-Control-Allow-Origin': '*'
    });
    res.end(fileContent);
    return;
  }

  if (method === 'POST' && pathname === '/api/v1/user/update') {
    const body = await parseBody(req);
    const authHeader = req.headers['authorization'];
    
    console.log('Authorization header:', authHeader);
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      console.log('未授权：缺少Bearer token');
      sendResponse(res, 401, { success: false, message: '未授权' });
      return;
    }
    
    const token = authHeader.split(' ')[1];
    console.log('Token:', token);
    
    const tokenParts = token.split('_');
    console.log('Token parts:', tokenParts);
    
    let userId = tokenParts[2] ? 'user_' + tokenParts[2] : null;
    
    if (!userId || !userDatabase[userId]) {
      console.log('用户不存在或token无效，使用第一个模拟用户');
      userId = Object.keys(userDatabase)[0] || 'user_' + Date.now();
    }
    
    console.log('最终使用的userId:', userId);
    console.log('userDatabase中的用户:', Object.keys(userDatabase));
    
    console.log(`更新用户信息: ${userId}`, JSON.stringify(body));
    
    const allowedFields = ['avatarURL', 'nickname', 'phone_number'];
    const updateData = {};
    
    allowedFields.forEach(field => {
      if (body[field] !== undefined) {
        updateData[field] = body[field];
      }
    });
    
    userDatabase[userId] = {
      ...userDatabase[userId],
      ...updateData
    };
    
    saveUserDatabase();
    
    sendResponse(res, 200, {
      success: true,
      message: '用户信息更新成功',
      user: {
        user_id: userDatabase[userId].user_id,
        nickname: userDatabase[userId].nickname,
        avatarURL: userDatabase[userId].avatarURL,
        role: userDatabase[userId].role,
        points: userDatabase[userId].points || 0,
        phone_number: userDatabase[userId].phone_number || '',
        level: userDatabase[userId].level || 1
      }
    });
    return;
  }

  if (method === 'POST' && pathname === '/api/v1/ai/recognize') {
    console.log('AI识别请求');
    
    const mockResults = [
      {
        breed: '中华田园猫（橘猫）',
        character: '性格温顺，适应能力强',
        intelligence: '较高',
        lifespan: '12-15年'
      },
      {
        breed: '流浪犬（混血）',
        character: '忠诚友好，需要注意狂犬疫苗',
        intelligence: '中等',
        lifespan: '10-12年'
      },
      {
        breed: '中华田园猫（三花）',
        character: '活泼好动，绝大多数为母猫',
        intelligence: '较高',
        lifespan: '12-15年'
      }
    ];
    
    const result = mockResults[Math.floor(Math.random() * mockResults.length)];
    
    sendResponse(res, 200, {
      success: true,
      data: result
    });
    return;
  }

  if (method === 'GET' && pathname === '/api/v1/animals/search') {
    sendResponse(res, 200, {
      success: true,
      data: mockAnimals,
      total: mockAnimals.length
    });
    return;
  }

  if (method === 'POST' && pathname === '/api/v1/adoption/apply') {
    const body = await parseBody(req);
    console.log('领养申请:', JSON.stringify(body));
    
    sendResponse(res, 200, {
      success: true,
      message: '领养申请提交成功，工作人员将尽快联系您'
    });
    return;
  }

  if (method === 'GET' && pathname === '/api/v1/adoption/my-records') {
    sendResponse(res, 200, {
      success: true,
      data: [
        {
          id: 1,
          petName: '小橘',
          applyTime: '2024-01-15',
          status: 'pending',
          statusText: '审核中'
        }
      ]
    });
    return;
  }

  if (method === 'POST' && pathname === '/api/v1/rescue/records') {
    const body = await parseBody(req);
    console.log('救助记录:', JSON.stringify(body));
    
    sendResponse(res, 200, {
      success: true,
      message: '救助报备成功，志愿者将尽快前往',
      recordId: 'R' + Date.now()
    });
    return;
  }

  if (method === 'GET' && pathname === '/api/v1/rescue/my-records') {
    sendResponse(res, 200, {
      success: true,
      data: [
        {
          id: 1,
          title: '图书馆受伤橘猫',
          location: '西科大图书馆',
          time: '2024-01-15',
          status: 'completed',
          statusText: '已完成'
        }
      ]
    });
    return;
  }

  if (method === 'POST' && pathname === '/api/v1/community/posts') {
    const body = await parseBody(req);
    console.log('发布帖子:', JSON.stringify(body));
    
    sendResponse(res, 200, {
      success: true,
      message: '帖子发布成功'
    });
    return;
  }

  if (method === 'GET' && pathname === '/api/v1/community/posts') {
    sendResponse(res, 200, {
      success: true,
      data: mockCommunityPosts
    });
    return;
  }

  if (method === 'GET' && pathname === '/api/v1/tasks/volunteer') {
    sendResponse(res, 200, {
      success: true,
      data: mockVolunteerTasks
    });
    return;
  }

  if (method === 'POST' && pathname.startsWith('/api/v1/tasks/') && pathname.endsWith('/accept')) {
    const taskId = pathname.split('/')[4];
    console.log(`志愿者接单: ${taskId}`);
    
    sendResponse(res, 200, {
      success: true,
      message: '接单成功'
    });
    return;
  }

  if (method === 'POST' && pathname.startsWith('/api/v1/tasks/') && pathname.endsWith('/reject')) {
    const taskId = pathname.split('/')[4];
    console.log(`志愿者拒单: ${taskId}`);
    
    sendResponse(res, 200, {
      success: true,
      message: '已拒单'
    });
    return;
  }

  if (method === 'POST' && pathname === '/api/v1/volunteer/apply') {
    const body = await parseBody(req);
    console.log('志愿者申请:', JSON.stringify(body));
    
    sendResponse(res, 200, {
      success: true,
      message: '志愿者申请已提交，请耐心等待审核'
    });
    return;
  }

  if (method === 'GET' && pathname === '/api/v1/volunteer/status') {
    sendResponse(res, 200, {
      success: true,
      status: 'pending',
      statusText: '审核中'
    });
    return;
  }

  if (method === 'GET' && pathname === '/api/v1/donation/projects') {
    sendResponse(res, 200, {
      success: true,
      data: mockDonationProjects
    });
    return;
  }

  if (method === 'POST' && pathname === '/api/v1/donation/pay') {
    const body = await parseBody(req);
    console.log('捐款:', JSON.stringify(body));
    
    sendResponse(res, 200, {
      success: true,
      message: '捐款成功，感谢您的爱心'
    });
    return;
  }

  if (method === 'GET' && pathname === '/api/v1/donation/my-records') {
    sendResponse(res, 200, {
      success: true,
      data: [
        {
          id: 1,
          projectName: '流浪猫医疗救助基金',
          amount: 50,
          time: '2024-01-20'
        }
      ]
    });
    return;
  }

  if (method === 'GET' && pathname === '/api/v1/points/my-points') {
    sendResponse(res, 200, {
      success: true,
      points: 2580
    });
    return;
  }

  if (method === 'GET' && pathname === '/api/v1/points/products') {
    sendResponse(res, 200, {
      success: true,
      data: [
        {
          id: 1,
          name: '宠物罐头零食',
          description: '优质鸡肉配方，营养均衡',
          points: 500,
          image: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=pet%20food%20can&image_size=square'
        },
        {
          id: 2,
          name: '猫咪逗猫棒',
          description: '彩色羽毛，增添乐趣',
          points: 300,
          image: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=cat%20toy%20feather&image_size=square'
        },
        {
          id: 3,
          name: '宠物饮水机',
          description: '循环过滤，保持水质新鲜',
          points: 2000,
          image: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=pet%20water%20fountain&image_size=square'
        }
      ]
    });
    return;
  }

  if (method === 'POST' && pathname === '/api/v1/points/exchange') {
    const body = await parseBody(req);
    console.log('积分兑换:', JSON.stringify(body));
    
    sendResponse(res, 200, {
      success: true,
      message: '兑换成功，商品将尽快配送'
    });
    return;
  }

  if (method === 'GET' && pathname === '/api/v1/points/exchange-records') {
    sendResponse(res, 200, {
      success: true,
      data: [
        {
          id: 1,
          productName: '宠物罐头零食',
          exchangeTime: '2024-01-15 14:30',
          points: 500,
          status: 'completed',
          statusText: '已完成'
        }
      ]
    });
    return;
  }

  if (method === 'POST' && pathname === '/api/v1/reimbursement/apply') {
    const body = await parseBody(req);
    console.log('报销申请:', JSON.stringify(body));
    
    sendResponse(res, 200, {
      success: true,
      message: '报销申请已提交'
    });
    return;
  }

  if (method === 'GET' && pathname === '/api/v1/reimbursement/my-records') {
    sendResponse(res, 200, {
      success: true,
      data: [
        {
          id: 1,
          typeText: '医疗费用',
          taskName: '救助受伤橘猫',
          amount: '150.00',
          status: 'approved',
          statusText: '已通过',
          applyTime: '2024-01-20 14:30'
        }
      ]
    });
    return;
  }

  if (method === 'GET' && pathname === '/api/v1/admin/dashboard/stats') {
    sendResponse(res, 200, {
      success: true,
      data: {
        totalUsers: 1256,
        totalRescues: 342,
        totalDonations: 28900,
        activeVolunteers: 156
      }
    });
    return;
  }

  if (method === 'GET' && pathname === '/api/v1/admin/users') {
    sendResponse(res, 200, {
      success: true,
      data: mockUsers.map(u => ({
        user_id: u.user_id,
        nickname: u.nickname,
        avatarURL: u.avatarURL,
        role: u.role,
        phone: u.phone
      }))
    });
    return;
  }

  if (method === 'PUT' && pathname.startsWith('/api/v1/admin/users/') && pathname.includes('/role')) {
    const userId = pathname.split('/')[4];
    const body = await parseBody(req);
    console.log(`修改用户角色: ${userId} -> ${body.role}`);
    
    sendResponse(res, 200, {
      success: true,
      message: '角色修改成功'
    });
    return;
  }

  if (method === 'GET' && pathname === '/api/v1/admin/volunteer-applications') {
    sendResponse(res, 200, {
      success: true,
      data: [
        {
          userId: 'u002',
          nickname: '校园铲屎官',
          phone: '13800138002',
          applyTime: '2024-01-20',
          status: 'pending'
        }
      ]
    });
    return;
  }

  if (method === 'GET' && pathname === '/api/v1/admin/rescue-records') {
    sendResponse(res, 200, {
      success: true,
      data: mockAnimals
    });
    return;
  }

  if (method === 'GET' && pathname === '/api/v1/admin/adoption-applications') {
    sendResponse(res, 200, {
      success: true,
      data: [
        {
          id: 1,
          petName: '小橘',
          applicant: '张三',
          applyTime: '2024-01-20',
          status: 'pending'
        }
      ]
    });
    return;
  }

  if (method === 'GET' && pathname === '/api/v1/admin/animals') {
    sendResponse(res, 200, {
      success: true,
      data: mockAnimals
    });
    return;
  }

  if (method === 'GET' && pathname === '/api/v1/admin/donation/public') {
    sendResponse(res, 200, {
      success: true,
      data: [
        {
          id: 1,
          title: '2024年1月资金使用公示',
          content: '本月共收到捐款5000元，用于医疗救助支出3000元...',
          publishTime: '2024-02-01'
        }
      ]
    });
    return;
  }

  if (method === 'GET' && pathname === '/api/v1/admin/financial/records') {
    sendResponse(res, 200, {
      success: true,
      data: [
        {
          id: 1,
          type: 'income',
          amount: 500,
          description: '用户捐款',
          time: '2024-01-20 14:30'
        },
        {
          id: 2,
          type: 'expense',
          amount: 200,
          description: '医疗费用报销',
          time: '2024-01-20 10:00'
        }
      ]
    });
    return;
  }

  if (method === 'GET' && pathname === '/api/v1/admin/community/pending-posts') {
    sendResponse(res, 200, {
      success: true,
      data: mockCommunityPosts
    });
    return;
  }

  if (method === 'GET' && pathname === '/api/v1/admin/products') {
    sendResponse(res, 200, {
      success: true,
      data: [
        {
          id: 1,
          name: '宠物罐头零食',
          points: 500,
          stock: 50
        }
      ]
    });
    return;
  }

  if (method === 'GET' && pathname === '/api/v1/admin/points/exchange-records') {
    sendResponse(res, 200, {
      success: true,
      data: [
        {
          id: 1,
          userNickname: '爱心志愿者',
          productName: '宠物罐头零食',
          points: 500,
          exchangeTime: '2024-01-20 14:30'
        }
      ]
    });
    return;
  }

  if (method === 'GET' && pathname === '/api/v1/admin/permissions') {
    sendResponse(res, 200, {
      success: true,
      data: {
        role: 'admin',
        permissions: ['user_management', 'rescue_management', 'adoption_management', 'donation_management', 'community_management', 'points_management', 'system_config']
      }
    });
    return;
  }

  if (method === 'GET' && pathname === '/api/v1/admin/audit/logs') {
    sendResponse(res, 200, {
      success: true,
      data: [
        {
          id: 1,
          admin: '管理员小王',
          action: '修改用户角色',
          target: '用户001',
          time: '2024-01-20 14:30'
        }
      ]
    });
    return;
  }

  console.log(`未匹配的路由: ${method} ${pathname}`);
  sendResponse(res, 404, { error: 'Not Found' });
});

server.listen(PORT, HOST, () => {
  console.log(`\n🚀 服务器运行在 http://0.0.0.0:${PORT}`);
  console.log(`📱 API 基础地址: http://localhost:${PORT}/api/v1`);
  console.log(`\n测试账号:`);
  console.log(`  手机号: 13800138001`);
  console.log(`  密码: 123456`);
  console.log(`  (志愿者账号)`);
  console.log(`\n  手机号: 13800138002`);
  console.log(`  密码: 123456`);
  console.log(`  (普通用户)`);
  console.log(`\n  手机号: 13800138003`);
  console.log(`  密码: 123456`);
  console.log(`  (管理员)`);
  console.log(`\n等待请求...`);
});
