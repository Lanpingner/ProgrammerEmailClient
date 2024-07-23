const HyperExpress = require('hyper-express');
const Database = require('./database');
const dbconfig_email = require('./dbconfig_email');
const webserver = new HyperExpress.Server();

const specific_middleware1 = (request, response, next) => {
    console.log(request.headers.host);
    return next();
};

const corsMiddleware = async (request, response, next) => {
    response.setHeader('Vary', 'Origin');
    response.setHeader('Access-Control-Allow-Origin', '*');
    response.setHeader('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization');
    response.setHeader('Access-Control-Allow-Methods', 'OPTIONS, POST, GET, PUT, DELETE');
    response.setHeader('Access-Control-Allow-Credentials', 'true');

    if (request.method === 'OPTIONS') {
        response.status(204).send();
    } else {
        next();
    }
};

webserver.get('/',
    { middlewares: [specific_middleware1, corsMiddleware] },
    (request, response) => {
        response.send('Hello World');
    }
);

// Fetch tags endpoint
webserver.get('/tags',
    { middlewares: [specific_middleware1, corsMiddleware] },
    async (req, res) => {
        const db = new Database(dbconfig_email);

        try {
            await db.connect();
            const tags = await db.query(`SELECT DISTINCT unnest(tags) AS tag FROM email_storage.emails`);
            await db.disconnect();
            res.status(200).json(tags.map(tag => tag.tag));
        } catch (error) {
            console.error('Database query error:', error);
            res.status(500).json({ error: 'Internal Server Error' });
        }
    }
);

// Fetch emails with optional tag filtering and search query endpoint
webserver.get("/emails",
    { middlewares: [specific_middleware1, corsMiddleware] },
    async (req, res) => {
        const db = new Database(dbconfig_email);
        const page = parseInt(req.query.page) || 1;
        const limit = parseInt(req.query.limit) || 20;
        const offset = (page - 1) * limit;
        const searchQuery = req.query.search || '';

        try {
            await db.connect();

            let query = `SELECT id, folder_id, email_id, subject, flags, tags, reply_to, email_date, reference, attachments, email_from, email_to, cc, bcc 
                         FROM email_storage.emails `;

            const conditions = [];

            if (searchQuery) {
                const searchConditions = [];
                const searchTerms = searchQuery.split(' ');
                console.log(searchTerms);
                searchTerms.forEach(term => {
                    const [field, value] = term.split(':');
                    if (field && value) {
                        if (field === 'tags') {
                            const tagsArray = value.split(',');
                            const tagConditions = tagsArray.map(tag => `'${tag}' = ANY(tags)`);
                            searchConditions.push(`(${tagConditions.join(' OR ')})`);
                        } else {
                            searchConditions.push(`${field}::text ILIKE '%${value}%'`);
                        }
                    }
                });
                if (searchConditions.length > 0) {
                    conditions.push(searchConditions.join(' AND '));
                }
            }

            if (conditions.length > 0) {
                query += `WHERE ${conditions.join(' AND ')}`;
            }
            console.log(query);

            query += ` ORDER BY email_date`;

            const dbdata = await db.query(query);
            await db.disconnect();
            res.status(200).json(dbdata);
        } catch (error) {
            console.error('Database query error:', error);
            res.status(500).json({ error: 'Internal Server Error' });
        }
    }
);

// Activate webserver by calling .listen(port, callback);
webserver.listen(3001)
    .then(() => console.log('Webserver started on port 3001'))
    .catch((error) => console.log('Failed to start webserver on port 3001:', error));

