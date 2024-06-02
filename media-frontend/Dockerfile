# Use an official Node.js runtime as a parent image
FROM node:22-alpine

## Create a user to run the app in Container Apps
#RUN addgroup -g 1000 appuser \
#    && adduser -u 1000 -G appuser -s /bin/sh -D appuser

# Set the working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json to the working directory
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code to the working directory
COPY . .

# # Build the React application
# RUN npm run build

# # Install a simple web server to serve the React app
# RUN npm install -g serve

# # Set the command to run the web server on port 3000
# CMD ["serve", "-s", "build", "-l", "3000"]

## Allow the user to create files in the main directory
RUN chown -R 1000 /app

CMD ["npm", "start"]

# Expose port 3000 to the outside world
EXPOSE 3000
