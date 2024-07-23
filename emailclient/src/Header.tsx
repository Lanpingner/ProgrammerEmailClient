import React from 'react';
import './Header.css';

interface HeaderProps {
    tags: string[];
    selectedTag: string;
    onTagClick: (tag: string) => void;
}

const Header: React.FC<HeaderProps> = ({ tags, selectedTag, onTagClick }) => {
    return (
        <div className="header">
            {tags.map(tag => (
                <button
                    key={tag}
                    className={`tag ${tag === selectedTag ? 'selected' : ''}`}
                    onClick={() => onTagClick(tag)}
                >
                    {tag}
                </button>
            ))}
        </div>
    );
};

export default Header;

