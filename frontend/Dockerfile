# Use the official lightweight Node.js image
FROM node:18-alpine

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and install dependencies
COPY package*.json ./
RUN npm install

# Copy the rest of your frontend code
COPY . .

# Expose the port your frontend runs on
EXPOSE 3000

# Command to start your React app
CMD ["npm", "run", "dev", "--", "--host"]
