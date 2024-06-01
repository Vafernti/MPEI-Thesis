import React, { useContext, useEffect, useState } from "react";
import ErrorMessage from "./ErrorMessage";
import { UserContext } from "../context/UserContext";
import UploadModal from "./UploadModal";
import TrackInfoModal from "./TrackInfoModal";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faDownload, faTrash } from '@fortawesome/free-solid-svg-icons';

const Table = () => {
    const [token] = useContext(UserContext);
    const [media, setMedia] = useState([]);
    const [errorMessage, setErrorMessage] = useState("");
    const [loading, setLoading] = useState(true);
    const [sortConfig, setSortConfig] = useState({ key: 'title', direction: 'ascending' });
    const [showUploadModal, setShowUploadModal] = useState(false);
    const [showTrackInfoModal, setShowTrackInfoModal] = useState(false);
    const [selectedTrack, setSelectedTrack] = useState(null);
    const [searchQuery, setSearchQuery] = useState("");

    const getMedia = async () => {
        setLoading(true);
        const requestOptions = {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
            },
        };

        try {
            const response = await fetch("/api/media/", requestOptions);

            if (!response.ok) {
                throw new Error("Something went wrong. Couldn't load the media.");
            }

            const data = await response.json();
            setMedia(data);
        } catch (error) {
            setErrorMessage(error.message);
        } finally {
            setLoading(false);
        }
    };

    const searchMedia = async (query) => {
        setLoading(true);
        const requestOptions = {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
            },
        };

        try {
            const response = await fetch(`/api/media/search?query=${query}`, requestOptions);

            if (!response.ok) {
                throw new Error("Something went wrong. Couldn't load the media.");
            }

            const data = await response.json();
            setMedia(data);
        } catch (error) {
            setErrorMessage(error.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        getMedia();
    }, [token]);

    const sortedMedia = [...media].sort((a, b) => {
        if (a[sortConfig.key] < b[sortConfig.key]) {
            return sortConfig.direction === 'ascending' ? -1 : 1;
        }
        if (a[sortConfig.key] > b[sortConfig.key]) {
            return sortConfig.direction === 'ascending' ? 1 : -1;
        }
        return 0;
    });

    const requestSort = (key) => {
        let direction = 'ascending';
        if (sortConfig.key === key && sortConfig.direction === 'ascending') {
            direction = 'descending';
        }
        setSortConfig({ key, direction });
    };

    const getSortIndicator = (key) => {
        if (sortConfig.key === key) {
            return sortConfig.direction === 'ascending' ? '▲' : '▼';
        }
        return '';
    };

    const downloadMedia = async (title) => {
        const requestOptions = {
            method: "GET",
            headers: {
                Authorization: `Bearer ${token}`,
            },
        };

        try {
            const response = await fetch(`/api/download/${title}`, requestOptions);
            if (!response.ok) {
                throw new Error("Download failed.");
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = title;
            document.body.appendChild(a);
            a.click();
            a.remove();
        } catch (error) {
            setErrorMessage(error.message);
        }
    };

    const deleteMedia = async (title) => {
        const requestOptions = {
            method: "DELETE",
            headers: {
                Authorization: `Bearer ${token}`,
            },
        };

        try {
            const response = await fetch(`/api/delete/${title}`, requestOptions);
            if (!response.ok) {
                throw new Error("Delete failed.");
            }
            setMedia(media.filter((item) => item.title !== title));
        } catch (error) {
            setErrorMessage(error.message);
        }
    };

    const convertToLocalTime = (utcTime) => {
        const date = new Date(utcTime);
        return date.toLocaleString(); // This will convert to user's local time
    };

    const handleSearch = (e) => {
        const query = e.target.value;
        setSearchQuery(query);
        if (query) {
            searchMedia(query);
        } else {
            getMedia();
        }
    };

    const handleRowClick = (track) => {
        setSelectedTrack(track);
        setShowTrackInfoModal(true);
    };

    return (
        <div style={{ width: '100%', overflowX: 'auto' }}>
            <button
                className="button is-fullwidth mb-5 is-primary"
                onClick={() => setShowUploadModal(true)}
            >
                Add Media
            </button>
            <input
                type="text"
                className="input mb-3"
                placeholder="Search..."
                value={searchQuery}
                onChange={handleSearch}
            />
            <ErrorMessage message={errorMessage} />
            {loading ? (
                <p>Loading...</p>
            ) : (
                <div className="table-container">
                    <table className="table is-fullwidth is-striped">
                        <thead>
                            <tr>
                                <th onClick={() => requestSort('title')} style={{ cursor: 'pointer' }}>
                                    Title {getSortIndicator('title')}
                                </th>
                                <th onClick={() => requestSort('length')} style={{ cursor: 'pointer' }}>
                                    Length {getSortIndicator('length')}
                                </th>
                                <th onClick={() => requestSort('artist_name')} style={{ cursor: 'pointer' }}>
                                    Artist {getSortIndicator('artist_name')}
                                </th>
                                <th onClick={() => requestSort('album_name')} style={{ cursor: 'pointer' }}>
                                    Album {getSortIndicator('album_name')}
                                </th>
                                <th onClick={() => requestSort('genre')} style={{ cursor: 'pointer' }}>
                                    Genre {getSortIndicator('genre')}
                                </th>
                                <th onClick={() => requestSort('time')} style={{ cursor: 'pointer' }}>
                                    Date Added {getSortIndicator('time')}
                                </th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {sortedMedia.map((item) => (
                                <tr key={item.id} onClick={() => handleRowClick(item)} style={{ cursor: 'pointer' }}>
                                    <td>{item.title}</td>
                                    <td>{item.length}</td>
                                    <td>{item.artist_name}</td>
                                    <td>{item.album_name}</td>
                                    <td>{item.genre}</td>
                                    <td>{convertToLocalTime(item.time)}</td>
                                    <td style={{ display: 'flex', justifyContent: 'space-around' }}>
                                        <button
                                            className="button is-light"
                                            onClick={(e) => { e.stopPropagation(); downloadMedia(item.title); }}
                                            title="Download"
                                            style={{ backgroundColor: 'blue', color: 'white' }}
                                        >
                                            <FontAwesomeIcon icon={faDownload} />
                                        </button>
                                        <button
                                            className="button is-light"
                                            onClick={(e) => { e.stopPropagation(); deleteMedia(item.title); }}
                                            title="Delete"
                                            style={{ backgroundColor: 'red', color: 'white' }}
                                        >
                                            <FontAwesomeIcon icon={faTrash} />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
            {showUploadModal && (
                <UploadModal
                    onClose={() => setShowUploadModal(false)}
                    onUpload={getMedia}
                />
            )}
            {showTrackInfoModal && (
                <TrackInfoModal
                    track={selectedTrack}
                    onClose={() => setShowTrackInfoModal(false)}
                />
            )}
        </div>
    );
};

export default Table;
