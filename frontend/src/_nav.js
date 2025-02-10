export default [
  {
    component: 'CNavTitle',
    name: 'Setup',
  },
  {
    component: 'CNavItem',
    name: 'Locations',
    to: '/locations',
    icon: 'cil-speedometer',
    badge: {
      color: 'primary',
      text: 'NEW',
    },
  },

  {
    component: 'CNavTitle',
    name: 'Target Search',
  },
  {
    component: 'CNavItem',
    name: 'Target Search',
    to: '/search',
    icon: 'cil-cursor',
  },
  {
    component: 'CNavItem',
    name: 'Target Audit',
    to: '/audit',
    icon: 'cil-cursor',
  },

  {
    component: 'CNavTitle',
    name: 'Route Planning',
  },
  {
    component: 'CNavItem',
    name: 'Planner',
    to: '/planner',
    icon: 'cil-cursor',
  },
 
]
