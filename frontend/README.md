# React + Vite

В формах **Add product** и **Edit product** фотографию можно выбрать с компьютера.
Поддерживаются JPEG, PNG, WebP и GIF до 5 МБ, есть предпросмотр и **Remove photo**.
Фото отправляется вместе с полями формы и хранится в PostgreSQL на backend.
Переменная `VITE_API_URL` задаёт адрес backend (по умолчанию `http://127.0.0.1:8000`);
она также используется для загрузки сохранённых фотографий в каталоге.

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and Oxlint's TypeScript related rules in your project.
