import React, { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
    faArchive, faReply, faChevronDown, faChevronUp,
    faThumbtack, faEye, faTrashCan, faSyncAlt, faSearch, faExternalLinkAlt
} from '@fortawesome/free-solid-svg-icons';
import Email from './email';
import './EmailList.css';

interface EmailListProps {
    emails: Email[];
    onEmailClick: (email: Email) => void;
}

const EmailList: React.FC<EmailListProps> = ({ emails, onEmailClick }) => {
    const [expandedEmailId, setExpandedEmailId] = useState<number | null>(null);

    const handleExpandClick = (emailId: number) => {
        setExpandedEmailId(expandedEmailId === emailId ? null : emailId);
    };

    return (
        <aside className="sidebar">
            <div className="email-list">
                {emails?.map(email => (
                    <div key={email.id} className="email-item">
                        <div className="email-summary">
                            <input type="checkbox" className="email-checkbox" />
                            <FontAwesomeIcon icon={faThumbtack} className="icon pin" />
                            <FontAwesomeIcon icon={faEye} className="icon view" />
                            <button className="icon-expand" onClick={() => handleExpandClick(email.id)}>
                                <FontAwesomeIcon icon={expandedEmailId === email.id ? faChevronUp : faChevronDown} />
                            </button>
                            <span className="email-subject" onClick={() => onEmailClick(email)}>
                                {email.subject}
                            </span>
                            <span className="email-date">{new Date(email.email_date).toLocaleDateString()}</span>
                            <FontAwesomeIcon icon={faExternalLinkAlt} className="top-bar-icon" />
                        </div>
                        {expandedEmailId === email.id && (
                            <div className="email-details">
                                <a href="#" className="icon reply">
                                    <FontAwesomeIcon icon={faReply} /> Reply
                                </a>
                                <a href="#" className="icon archive">
                                    <FontAwesomeIcon icon={faArchive} />
                                    Archive
                                </a>
                                <a href="#" className="icon archive">
                                    <FontAwesomeIcon icon={faTrashCan} />
                                    Delete
                                </a>
                                <p><strong>From:</strong> {email.email_from.name} &lt;{email.email_from.address}&gt;</p>
                                {email.email_to && <p><strong>To:</strong> {email.email_to.accounts?.map(acc => `${acc.name} <${acc.address}>`).join(', ')} </p>}
                                {email.cc && <p><strong>CC:</strong> {email.cc.accounts?.map(acc => `${acc.name} <${acc.address}>`).join(', ')}</p>}
                                {email.bcc && <p><strong>BCC:</strong> {email.bcc.accounts?.map(acc => `${acc.name} <${acc.address}>`).join(', ')}</p>}
                                <p><strong>Date:</strong> {new Date(email.email_date).toLocaleString()}</p>
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </aside>
    );
};

export default EmailList;

