import React, { useContext, useEffect, useState } from "react";
import ErrorMessage from "./ErrorMessage";
import { UserContext } from "../context/UserContext";
import UploadModal from "./UploadModal";

const Table = () => {
    const [token] = useContext(UserContext);
    const [media, setMedia] = useState([]);
    const [errorMessage, setErrorMessage] = useState("");
    const [loading, setLoading] = useState(true);
    const [sortConfig, setSortConfig] = useState({ key: 'title', direction: 'ascending' });
    const [showUploadModal, setShowUploadModal] = useState(false);

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

    return (
        <>
            <button
                className="button is-fullwidth mb-5 is-primary"
                onClick={() => setShowUploadModal(true)}
            >
                Add Media
            </button>
            <ErrorMessage message={errorMessage} />
            {loading ? (
                <p>Loading...</p>
            ) : (
                <table className="table is-fullwidth">
                    <thead>
                        <tr>
                            <th onClick={() => requestSort('title')}>Title</th>
                            <th onClick={() => requestSort('length')}>Length</th>
                            <th onClick={() => requestSort('artist_id')}>Artist</th>
                            <th onClick={() => requestSort('album_id')}>Album</th>
                            <th onClick={() => requestSort('genre')}>Genre</th>
                            <th onClick={() => requestSort('time')}>Date Added</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {sortedMedia.map((item) => (
                            <tr key={item.id}>
                                <td>{item.title}</td>
                                <td>{item.length}</td>
                                <td>{item.artist_name}</td>
                                <td>{item.album_name}</td>
                                <td>{item.genre}</td>
                                <td>{item.time}</td>
                                <td>
                                    <button
                                        className="button mr-2 is-info is-light"
                                        onClick={() => downloadMedia(item.title)}
                                    >
                                        Download
                                    </button>
                                    <button
                                        className="button mr-2 is-danger is-light"
                                        onClick={() => deleteMedia(item.title)}
                                    >
                                        Delete
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
            {showUploadModal && (
                <UploadModal
                    onClose={() => setShowUploadModal(false)}
                    onUpload={getMedia}
                />
            )}
        </>
    );
};

export default Table;
