FROM node:22-slim

WORKDIR /srv/library-lending
COPY package.json ./
RUN npm install --omit=dev
COPY dist/ ./dist/

USER node
EXPOSE 3000
CMD ["node", "dist/main/server.js"]
