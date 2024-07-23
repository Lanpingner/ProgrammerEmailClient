module.exports = {
    user: "postgres",
    host: process.env.DB_HOST || "172.18.0.1", // Use the DB_HOST environment variable if set, otherwise use the default value
    database: "emaildb",
    password: process.env.DB_PASS,
    port: 5433,
};
