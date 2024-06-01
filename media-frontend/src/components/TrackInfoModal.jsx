import React, { useContext } from "react";
import { UserContext } from "../context/UserContext";

const TrackInfoModal = ({ track, onClose }) => {
    const [token] = useContext(UserContext);

    if (!track) return null;

    // Construct the full URL for the media file and cover image
    const mediaUrl = `${window.location.origin}/api/stream/${track.title}?token=${token}`;
    const coverImageUrl = `${window.location.origin}/${track.cover_image}`;

    return (
        <div className="modal is-active">
            <div className="modal-background"></div>
            <div className="modal-content">
                <div className="box">
                    <h1 className="title">{track.title}</h1>
                    <p><strong>Artist:</strong> {track.artist_name}</p>
                    <p><strong>Album:</strong> {track.album_name}</p>
                    <p><strong>Genre:</strong> {track.genre}</p>
                    <img src={coverImageUrl} alt="Cover" style={{ width: '100%' }} />
                    <audio controls style={{ width: '100%' }}>
                        <source src={mediaUrl} type="audio/mpeg" />
                        Your browser does not support the audio element.
                    </audio>
                    <button className="button is-primary mt-3" onClick={onClose}>Close</button>
                </div>
            </div>
            <button className="modal-close is-large" onClick={onClose}></button>
        </div>
    );
};

export default TrackInfoModal;
