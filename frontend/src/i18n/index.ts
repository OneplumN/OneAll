import { createI18n } from 'vue-i18n';
import dayjs from 'dayjs';
import 'dayjs/locale/en';
import 'dayjs/locale/zh-cn';

const messages = {
  'zh-CN': {
    common: {
      appName: '多维运维平台',
      skipToContent: '跳到主内容',
      refresh: '刷新',
      create: '新建',
      search: '搜索',
      cancel: '取消',
      save: '保存',
      loadingFallback: '暂未连接后端接口，展示示例数据。',
      mockCreated: '示例数据已添加',
      mockExecuted: '执行已模拟完成'
    },
    auth: {
      loginTitle: '登录 {app}',
      username: '用户名',
      password: '密码',
      login: '登录',
      usernameRequired: '请输入用户名',
      passwordRequired: '请输入密码',
      invalidCredentials: '用户名或密码错误',
      backendUnavailable: '无法连接后端服务，请检查接口地址与网络',
      loginFailed: '登录失败，请稍后重试'
    },
    tools: {
      libraryTitle: '工具库',
      librarySubtitle: '集中管理脚本与运维工具，快速执行并沉淀经验。',
      createTool: '新增工具',
      dialogTitle: '新建工具',
      execute: '执行',
      viewDetails: '详情',
      toolCreated: '工具创建成功',
      toolExecuteTriggered: '执行已触发'
    },
    knowledge: {
      title: '知识库',
      subtitle: '沉淀故障案例、脚本说明与处理经验，助力快速响应。',
      createArticle: '新建文章',
      articleCreated: '文章创建成功',
      fallbackAdded: '示例文章已添加'
    },
    code: {
      title: '代码管理',
      subtitle: '集中维护脚本版本，支持在线上传、回滚与执行记录。',
      createRepo: '新建仓库',
      createRepoDialogTitle: '新建脚本仓库',
      uploadVersion: '上传版本',
      versionHistory: '版本历史',
      uploadDrawerTitle: '上传新版本',
      repoCreated: '仓库创建成功',
      fallbackRepo: '示例仓库已添加',
      versionUploaded: '版本上传成功',
      fallbackVersion: '示例版本已添加',
      rollbackSuccess: '已回滚到 {version}',
      rollbackMock: '模拟回滚成功（示例）: {version}'
    }
  },
  en: {
    common: {
      appName: 'Multi-dimensional Operations Platform',
      skipToContent: 'Skip to main content',
      refresh: 'Refresh',
      create: 'Create',
      search: 'Search',
      cancel: 'Cancel',
      save: 'Save',
      loadingFallback: 'Backend APIs are not connected yet. Showing sample data.',
      mockCreated: 'Sample data added',
      mockExecuted: 'Execution simulated successfully'
    },
    auth: {
      loginTitle: 'Sign in to {app}',
      username: 'Username',
      password: 'Password',
      login: 'Sign in',
      usernameRequired: 'Please enter your username',
      passwordRequired: 'Please enter your password',
      invalidCredentials: 'Invalid username or password',
      backendUnavailable: 'Cannot reach backend service. Check API base URL and network.',
      loginFailed: 'Login failed. Please try again.'
    },
    tools: {
      libraryTitle: 'Tool Library',
      librarySubtitle: 'Manage operational scripts centrally to execute and capture learnings quickly.',
      createTool: 'New Tool',
      dialogTitle: 'Create Tool',
      execute: 'Execute',
      viewDetails: 'Details',
      toolCreated: 'Tool created successfully',
      toolExecuteTriggered: 'Execution triggered'
    },
    knowledge: {
      title: 'Knowledge Base',
      subtitle: 'Capture incidents, script usage, and best practices to improve response.',
      createArticle: 'New Article',
      articleCreated: 'Article created successfully',
      fallbackAdded: 'Sample article added'
    },
    code: {
      title: 'Script Repository',
      subtitle: 'Maintain script versions, upload updates, and track rollbacks in one place.',
      createRepo: 'New Repository',
      createRepoDialogTitle: 'Create Repository',
      uploadVersion: 'Upload Version',
      versionHistory: 'Version History',
      uploadDrawerTitle: 'Upload New Version',
      repoCreated: 'Repository created successfully',
      fallbackRepo: 'Sample repository added',
      versionUploaded: 'Version uploaded successfully',
      fallbackVersion: 'Sample version added',
      rollbackSuccess: 'Rolled back to {version}',
      rollbackMock: 'Mock rollback success: {version}'
    }
  }
};

function resolveInitialLocale(): 'zh-CN' | 'en' {
  if (typeof window === 'undefined') {
    return 'zh-CN';
  }
  const stored = window.localStorage.getItem('oneall_locale');
  if (stored) {
    return stored === 'en' ? 'en' : 'zh-CN';
  }
  const navigatorLang = window.navigator.language;
  if (navigatorLang.toLowerCase().startsWith('zh')) {
    return 'zh-CN';
  }
  return 'en';
}

export const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: resolveInitialLocale(),
  fallbackLocale: 'en',
  messages
});

function syncDayjsLocale(locale: 'zh-CN' | 'en') {
  dayjs.locale(locale === 'zh-CN' ? 'zh-cn' : 'en');
}

syncDayjsLocale(i18n.global.locale.value as 'zh-CN' | 'en');

export function setLocale(locale: 'zh-CN' | 'en') {
  i18n.global.locale.value = locale;
  syncDayjsLocale(locale);
  if (typeof document !== 'undefined') {
    document.documentElement.lang = locale;
  }
  if (typeof window !== 'undefined') {
    window.localStorage.setItem('oneall_locale', locale);
  }
}

export const supportedLocales = [
  { value: 'zh-CN', label: '简体中文' },
  { value: 'en', label: 'English' }
];
