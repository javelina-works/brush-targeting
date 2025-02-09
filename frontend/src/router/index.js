import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '@/views/HomeView.vue'; // Avoid '@' for now
// import HomeView from '../views/HomeView.vue'; // Avoid "@/" for now

const routes = [
  { path: '/', name: 'Home', component: HomeView }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
