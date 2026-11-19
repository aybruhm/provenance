FROM dhi.io/node:25-debian13-sfw-dev

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

EXPOSE 3000

CMD ["sh", "-c", "npm run prepare && exec npm run dev"]