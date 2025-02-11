import { createRouter, createWebHistory } from 'vue-router';

import DefaultLayout from '@/layouts/DefaultLayout.vue';

import HomeView from '@/views/HomeView.vue'; // Avoid '@' for now
import Locations from '@/views/Locations.vue';
import AuditPage from '@/views/audit/AuditPage.vue';
import SearchPage from '@/views/SearchPage.vue';
import PlannerPage from '@/views/PlannerPage.vue';
import NotFound from '@/views/NotFound.vue';

const routes = [
  {
    path: '/',
    component: DefaultLayout,
    // component: HomeView,
    redirect: '/audit',
    children: [
        { path: '/locations', component: Locations },
        { path: '/search', component: SearchPage },
        { path: '/audit', component: AuditPage },
        { path: '/planner', component: PlannerPage },
        { path: '/:pathMatch(.*)*', component: NotFound }, // Catch-all 404
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
