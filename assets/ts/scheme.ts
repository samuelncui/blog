// Set the initial Stack colour scheme before rendering; no remote resources.
const key = 'StackColorScheme';
const scheme = localStorage.getItem(key) || 'auto';
document.documentElement.dataset.scheme = scheme === 'dark' ||
    (scheme === 'auto' && matchMedia('(prefers-color-scheme: dark)').matches) ? 'dark' : 'light';
