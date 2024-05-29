import React, { useState, useContext } from "react";
import { UserContext } from "../context/UserContext";
import ErrorMessage from "./ErrorMessage";

const UploadModal = ({ onClose, onUpload }) => {
    const [file, setFile] = useState(null);
    const [errorMessage, setErrorMessage] = useState("");
    const [loading, setLoading] = useState(false);
    const [token] = useContext(UserContext);

    const handleFileChange = (e) => {
        setFile(e.target.files[0]);
    };

    const handleUpload = async () => {
        if (!file) {
            setErrorMessage("Please select a file to upload.");
            return;
        }

        setLoading(true);
        setErrorMessage("");
        const formData = new FormData();
        formData.append("file", file);

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
                throw new Error(data.detail || "Failed to upload file");
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
                                onChange={handleFileChange}
                                className="input"
                            />
                        </div>
                    </div>
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
