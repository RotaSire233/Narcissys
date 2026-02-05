import React from 'react';
import PropTypes from 'prop-types';
import './CloseButton.css';

const CloseButton = ({ onClick }) => {
    return (
        <button className="close-button" onClick={onClick}>
            ×
        </button>
    );
};

CloseButton.propTypes = {
    onClick: PropTypes.func.isRequired,
};

export default CloseButton;