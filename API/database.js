const { Client } = require("pg");

class Database {
    constructor(config) {
        this.client = new Client(config);
        //console.log(config);
    }

    debugable() {
        if (process.env.SQL_DEBUG == "1") {
            return true;
        } else {
            return false;
        }
    }

    debugres() {
        if (process.env.SQL_DEBUG_RES == "1") {
            return true;
        } else {
            return false;
        }
    }

    async connect() {
        try {
            await this.client.connect();
            if (this.debugable() === true) {
            }
        } catch (error) {
            throw error;
        }
    }

    async disconnect() {
        try {
            await this.client.end();
        } catch (error) {
            throw error;
        }
    }

    async query(query) {
        try {
            //console.log(this.debugable());
            const result = await this.client.query(query);
            return result.rows;
        } catch (error) {
            throw error;
        }
    }

    async query_withparams(query, values, deepdebug) {
        try {
            const result = await this.client.query(query, values);
            return result.rows;
        } catch (error) {
            throw error;
        }
    }
}

module.exports = Database;
