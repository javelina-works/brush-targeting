import { createApp, h, provide } from 'vue';
import { createPinia } from 'pinia';

import App from './App.vue'
import router from './router';

import { ApolloClients, DefaultApolloClient } from "@vue/apollo-composable";
import apolloClient from "./apollo";

import CoreuiVue from '@coreui/vue'
import CIcon from '@coreui/icons-vue'
import { iconsSet as icons } from '@/assets/icons'

// import './style.css'
import 'leaflet/dist/leaflet.css';


const app = createApp({
    setup() {
      provide(DefaultApolloClient, apolloClient); // ✅ Explicitly provide Apollo Client
    },
    render: () => h(App),
  });

app.use(createPinia())
app.use(router)
app.use(CoreuiVue)
app.provide('icons', icons)
app.component('CIcon', CIcon)

app.mount('#app')
