import { createApp } from 'vue';
import { createPinia } from 'pinia';
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';
import 'element-plus/theme-chalk/dark/css-vars.css';
import zhCn from 'element-plus/es/locale/lang/zh-cn';

import App from './App.vue';
import router from './router';
import { installAuthGuard } from './router/guards';
import apiClient from './app/api/apiClient';
import { i18n, setLocale } from './i18n';
import './assets/main.css';
import './styles/theme.scss';
import { applyThemeMode, loadThemeMode } from './utils/theme';

applyThemeMode(loadThemeMode());

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
installAuthGuard(router, pinia);
app.use(router);
app.use(ElementPlus, { locale: zhCn });
app.use(i18n);
setLocale((i18n.global.locale.value as 'zh-CN' | 'en') ?? 'zh-CN');

app.provide('apiClient', apiClient);
app.config.globalProperties.$api = apiClient;

app.mount('#app');
