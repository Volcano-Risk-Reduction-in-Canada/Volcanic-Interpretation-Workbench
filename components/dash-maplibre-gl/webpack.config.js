const path = require('path');

module.exports = {
    entry: { main: './src/lib/index.js' },
    output: {
        path: path.resolve(__dirname, 'dash_maplibre_gl'),
        filename: 'dash_maplibre_gl.js',
        library: 'dash_maplibre_gl',
        libraryTarget: 'window',
    },
    externals: {
        react: 'React',
        'react-dom': 'ReactDOM',
    },
    module: {
        rules: [
            {
                test: /\.jsx?$/,
                exclude: /node_modules/,
                use: 'babel-loader',
            },
            {
                test: /\.css$/,
                use: ['style-loader', 'css-loader'],
            },
        ],
    },
    resolve: {
        extensions: ['.js', '.jsx'],
    },
    devtool: 'source-map',
};
