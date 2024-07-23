import React from 'react';
import Email from './email';

interface EmailViewerProps {
    email: Email | null;
}

const EmailViewer: React.FC<EmailViewerProps> = ({ email }) => {
    if (!email) {
        return <div className="email-viewer">Select an email to view</div>;
    }

    return (
        <div className="email-viewer">
            <h2>{email.subject}</h2>
            <p>{email.content}</p>
        </div>
    );
};

export default EmailViewer;

