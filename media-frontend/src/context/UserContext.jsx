import React, { createContext, useEffect, useState } from "react";

export const UserContext = createContext();

export const UserProvider = (props) => {
    const [token, setToken] = useState(localStorage.getItem("awsomeLeadsToken"));

    useEffect(() => {
        const fetchUser = async () => {
            if (!token) {
                localStorage.removeItem("awsomeLeadsToken");
                return;
            }

            const requestOptions = {
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: "Bearer " + token,
                },
            };

            try {
                const response = await fetch("/api/users/me", requestOptions);

                if (!response.ok) {
                    throw new Error("Failed to fetch user data");
                }

                const data = await response.json();
                console.log("User data fetched successfully", data);

            } catch (error) {
                console.error("Error fetching user data:", error);
                setToken(null);
                localStorage.removeItem("awsomeLeadsToken");
            }
        };

        fetchUser();
    }, [token]);

    useEffect(() => {
        if (token) {
            localStorage.setItem("awsomeLeadsToken", token);
        } else {
            localStorage.removeItem("awsomeLeadsToken");
        }
    }, [token]);

    return (
        <UserContext.Provider value={[token, setToken]}>
            {props.children}
        </UserContext.Provider>
    );
};
