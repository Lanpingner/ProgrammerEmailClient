import React, { useState, useEffect } from 'react';
import Header from './Header';
import EmailList from './EmailList';
import EmailViewer from './EmailViewer';
import Email from './email';
import './App.css';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
    faSyncAlt, faSearch, faExternalLinkAlt
} from '@fortawesome/free-solid-svg-icons';
import './TopBar.css';

const App: React.FC = () => {
    const [tags, setTags] = useState<string[]>([]);
    const [emails, setEmails] = useState<Email[]>([]);
    const [selectedTags, setSelectedTags] = useState<string[]>([]);
    const [selectedEmail, setSelectedEmail] = useState<Email | null>(null);
    const [searchQuery, setSearchQuery] = useState<string>('');
    const [autocompleteSuggestions, setAutocompleteSuggestions] = useState<string[]>(['date_from']);

    useEffect(() => {
        fetchTags();
    }, []);

    const fetchTags = async () => {
        const response = await fetch('http://localhost:3001/tags');
        const data = await response.json();
        setTags(data);
        if (data.length > 0) {
            setSelectedTags([data[0]]);
            const initialQuery = buildSearchQuery([data[0]], searchQuery);
            setSearchQuery(initialQuery);
            fetchEmails(initialQuery);
        }
    };

    const fetchEmails = async (query = '') => {
        const response = await fetch(`http://localhost:3001/emails?search=${encodeURIComponent(query)}`);
        const data = await response.json();
        setEmails(data);
    };

    const buildSearchQuery = (tags: string[], query: string) => {
        const tagsQuery = `tags:${tags.join(',')}`;
        return `${tagsQuery} ${query}`.trim();
    };

    const handleTagClick = (tag: string) => {
        const updatedTags = selectedTags.includes(tag)
            ? selectedTags.filter(t => t !== tag)
            : [...selectedTags, tag];
        setSelectedTags(updatedTags);
        const newSearchQuery = buildSearchQuery(updatedTags, searchQuery);
        setSearchQuery(newSearchQuery);
        fetchEmails(newSearchQuery);
    };

    const handleEmailClick = (email: Email) => {
        setSelectedEmail(email);
    };

    const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setSearchQuery(event.target.value);
    };

    const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
        if (event.key === 'Enter') {
            handleSearch();
        }
    };

    const handleSearch = () => {
        fetchEmails(searchQuery);
    };

    const handleSuggestionClick = (suggestion: string) => {
        setSearchQuery(suggestion);
        //fetchEmails(suggestion);
        //setAutocompleteSuggestions([]);
    };

    return (
        <div className="container">
            <Header tags={tags} selectedTag={selectedTags.join(', ')} onTagClick={handleTagClick} />
            <div className="content">
                <div className='LeftSide'>
                    <div className="top-bar">
                        <FontAwesomeIcon icon={faSyncAlt} className="top-bar-icon" />
                        <div className="search-bar">
                            <input type="text" placeholder=":threads :inbox" value={searchQuery} onChange={handleSearchChange} onKeyDown={handleKeyDown} />
                            <button className="search-button" onClick={handleSearch}>
                                <FontAwesomeIcon icon={faSearch} />
                            </button>
                        </div>
                        <span className="threads-info">6 of 6 threads</span>
                        <FontAwesomeIcon icon={faExternalLinkAlt} className="top-bar-icon" />
                    </div>
                    <EmailList emails={emails} onEmailClick={handleEmailClick} />
                </div>
                <div className='RightSide'>
                    {/*<div className="top-bar">
                        <FontAwesomeIcon icon={faSyncAlt} className="top-bar-icon" />
                        <div className="search-bar">
                            <input type="text" placeholder=":threads :inbox" value={searchQuery} onChange={handleSearchChange} />
                            <button className="search-button" onClick={handleSearch}>
                                <FontAwesomeIcon icon={faSearch} />
                            </button>
                        </div>
                        <span className="threads-info">6 of 6 threads</span>
                        <FontAwesomeIcon icon={faExternalLinkAlt} className="top-bar-icon" />
                    </div>*/}

                    <EmailViewer email={selectedEmail} />
                </div>
            </div>
        </div>
    );
};

export default App;

