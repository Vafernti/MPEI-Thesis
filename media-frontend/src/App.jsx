import React, { useState, useEffect, useContext } from 'react';
import Register from './components/Register';
import Header from './components/Header';
import Login from './components/Login';
import Table from './components/Table';
import { UserContext } from './context/UserContext';
import ErrorMessage from './components/ErrorMessage'; // Assuming you have an error message component

const App = () => {
  const [message, setMessage] = useState("");
  const [token] = useContext(UserContext);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const getWelcomeMessage = async () => {
    try {
      const response = await fetch("/api", {
        method: "GET",
        headers: {
          "Content-Type": "Application/json",
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to fetch welcome message");
      } else {
        setMessage(data.message);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getWelcomeMessage();
  }, []);

  return (
    <>
      <Header title={message} />
      <div className='columns'>
        <div className='column'></div>
        <div className='column m-5 is-two-thirds'>
          {loading ? (
            <p>Loading...</p>
          ) : error ? (
            <ErrorMessage message={error} />
          ) : (
            !token ? (
              <div className='columns'>
                <Register /> <Login />
              </div>
            ) : (
              <Table />
            )
          )}
        </div>
        <div className='column'></div>
      </div>
    </>
  );
};

export default App;
