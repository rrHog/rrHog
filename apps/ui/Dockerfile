FROM node:24-alpine

# Enable pnpm via Corepack
RUN corepack enable && corepack prepare pnpm@9 --activate

WORKDIR /app

# Install deps (use lockfile if present, otherwise generate it)
COPY package.json pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile || pnpm install --no-frozen-lockfile

# Copy source
COPY . .

EXPOSE 3000
# Ensure Next binds to container interface
CMD ["pnpm","exec","next","dev","-H","0.0.0.0","-p","3000"]