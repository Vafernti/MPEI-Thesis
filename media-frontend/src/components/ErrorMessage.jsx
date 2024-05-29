import React from "react";

const ErrorMessage = ({message}) => (
    <p className="has-text-weigtht-bold has-text-danger">
        {message}
    </p>
);

export default ErrorMessage;