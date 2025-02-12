import { createRouter, createWebHistory } from 'vue-router';

import DefaultLayout from '@/layouts/DefaultLayout.vue';
import HeadFootLayout from '@/layouts/HeadFootLayout.vue';

import HomeView from '@/views/HomeView.vue'; // Avoid '@' for now
import LocationJobManager from '@/views/locations/LocationJobManager.vue';

import UploadPage from '@/views/UploadPage.vue';
import AuditPage from '@/views/audit/AuditPage.vue';
import SearchPage from '@/views/search/SearchPage.vue';
import PlannerPage from '@/views/planner/PlannerPage.vue';
import NotFound from '@/views/NotFound.vue';

const routes = [
  {
    path: '/',
    name: 'Home',
    component: DefaultLayout,
    // component: HomeView,
    redirect: '/upload',
    children: [
        { path: '/upload', component: UploadPage },
        { path: '/search', name: "Target Search", component: SearchPage },
        { path: '/audit', name: "Target Audit", component: AuditPage },
        { path: '/planner', name: "Mission Planner", component: PlannerPage },
        { path: '/:pathMatch(.*)*', component: NotFound }, // Catch-all 404
    ],
  },
  {
    path: '/locations',
    name: "Locations",
    component: HeadFootLayout,
    children: [
      { path: '', name: "Select Location", component: LocationJobManager },
    ]
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
