export default {
  cacheDir: './vite-cache',
  resolve: { dedupe: ['react', 'react-dom'] },
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['probe.test.tsx'],
    maxWorkers: 1,
    fileParallelism: false,
    pool: 'forks',
  },
};
