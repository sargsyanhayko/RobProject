# React + Vite

В формах **Add product** и **Edit product** фотографию можно выбрать с компьютера.
Поддерживаются JPEG, PNG, WebP и GIF до 5 МБ, есть предпросмотр и **Remove photo**.
Фото отправляется вместе с полями формы и хранится в PostgreSQL на backend.
Переменная `VITE_API_URL` задаёт адрес backend (по умолчанию `http://127.0.0.1:8000`);
она также используется для загрузки сохранённых фотографий в каталоге.

На главной доступны Animals, Wall, 3D Wall, Home и Other. По умолчанию выбрана
Animals. Фильтрация идёт через `GET /api/products?category=…`. API-клиент
`getProducts(category?, { skip, limit, signal }?)` получает одну страницу,
а `getAllProducts` загружает все страницы выбранной категории. Запросы предыдущей
категории отменяются при переключении. На мобильном меню прокручивается по горизонтали.
В списке товаров `/admin` используются такие же вкладки категорий с фильтрацией
через API и Animals по умолчанию. Редактирование и удаление доступны в выбранной категории.

В формах администратора категория обязательна; доступны те же пять категорий.
Редактирование загружает текущую категорию товара. Можно задать Image URL или
выбрать локальное фото. Категория отправляется и в JSON, и при загрузке файла.
Подписи и значения категорий определены в одном `src/config/productCategories.js`.

Проверка: `npm run test`, `npm run lint`, `npm run build`.
Vitest проверяет переключение пяти категорий, выбор Animals по умолчанию, пустые категории, отмену устаревших
запросов, создание и редактирование, multipart-загрузку с категорией,
пагинацию API-клиента и сохранение Bearer JWT.

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and Oxlint's TypeScript related rules in your project.
