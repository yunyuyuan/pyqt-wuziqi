module.exports = {
    check_legal(s) {
        return s.match(/^[\u4E00-\u9FA5\w_]{1,16}$/)
    }
};