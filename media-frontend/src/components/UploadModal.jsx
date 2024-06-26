import React, { useState, useContext } from "react";
import { UserContext } from "../context/UserContext";
import ErrorMessage from "./ErrorMessage";

const UploadModal = ({ onClose, onUpload }) => {
    const [files, setFiles] = useState([]);
    const [errorMessage, setErrorMessage] = useState("");
    const [loading, setLoading] = useState(false);
    const [token] = useContext(UserContext);

    const handleFileChange = (e) => {
        setFiles(e.target.files);
    };

    const handleUpload = async () => {
        if (files.length === 0) {
            setErrorMessage("Please select at least one file to upload.");
            return;
        }

        setLoading(true);
        setErrorMessage("");
        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append("files", files[i]);
        }

        const requestOptions = {
            method: "POST",
            headers: {
                Authorization: `Bearer ${token}`,
            },
            body: formData,
        };

        try {
            const response = await fetch("/api/upload/", requestOptions);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Failed to upload files");
            }

            onUpload();
            onClose();
        } catch (error) {
            setErrorMessage(error.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="modal is-active">
            <div className="modal-background"></div>
            <div className="modal-content">
                <div className="box">
                    <h1 className="title">Add Media</h1>
                    <ErrorMessage message={errorMessage} />
                    <div className="field">
                        <div className="control">
                            <input
                                type="file"
                                accept=".m4a,.mp3,.wav,.flac,.aac"
                                onChange={handleFileChange}
                                className="input"
                                multiple
                            />
                        </div>
                    </div>
                    <p>Supported file types: .m4a, .mp3, .wav, .flac, .aac</p>
                    <button
                        className="button is-primary"
                        onClick={handleUpload}
                        disabled={loading}
                    >
                        {loading ? "Uploading..." : "Upload"}
                    </button>
                    <button className="button" onClick={onClose}>
                        Cancel
                    </button>
                </div>
            </div>
            <button className="modal-close is-large" onClick={onClose}></button>
        </div>
    );
};

export default UploadModal;
