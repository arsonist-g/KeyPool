import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue') },
  {
    path: '/',
    component: () => import('../views/Layout.vue'),
    children: [
      { path: '', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
      { path: 'keys', name: 'Keys', component: () => import('../views/Keys.vue') },
      { path: 'proxies', name: 'Proxies', component: () => import('../views/Proxies.vue') },
      { path: 'tokens', name: 'Tokens', component: () => import('../views/Tokens.vue') },
      { path: 'stats', name: 'Stats', component: () => import('../views/Stats.vue') },
      { path: 'guide', name: 'Guide', component: () => import('../views/Guide.vue') },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const token = localStorage.getItem('admin_token')
  if (!token && to.name !== 'Login') {
    return { name: 'Login' }
  }
})

export default router
