var currentCid = 1; // 当前分类 id
var cur_page = 1; // 当前页
var total_page = 1;  // 总页数
var data_querying = true;   // 是否正在向后台获取数据


$(function () {

    updateNewsData()
    // 首页分类切换
    $('.menu li').click(function () {
        var clickCid = $(this).attr('data-cid')
        $('.menu li').each(function () {
            $(this).removeClass('active')
        })
        $(this).addClass('active')

        if (clickCid != currentCid) {
            // 记录当前分类id
            currentCid = clickCid

            // 重置分页参数
            cur_page = 1
            total_page = 1
            updateNewsData()
        }
    })

    //页面滚动加载相关
    $(window).scroll(function () {

        // 浏览器窗口高度
        var showHeight = $(window).height();

        // 整个网页的高度
        var pageHeight = $(document).height();

        // 页面可以滚动的距离
        var canScrollHeight = pageHeight - showHeight;

        // 页面滚动了多少,这个是随着页面滚动实时变化的
        var nowScroll = $(document).scrollTop();

        if ((canScrollHeight - nowScroll) < 100) {
            if (!data_querying) {
                data_querying = true
                if (cur_page < total_page) {
                    cur_page += 1
                    updateNewsData()
                }
            }
        }
    })
})

function updateNewsData() {

    var params = {
        "cid": currentCid,
        "page": cur_page,
    }
    $.get("/news_list", params, function (response) {
        data_querying = false
        if (response.errno == "0") {
            total_page = response.data.total_page
            if (cur_page == 1){
                $(".list_con").html("")
            }
            for (var i = 0; i < response.data.news_dict_li.length; i++) {
                var news = response.data.news_dict_li[i]
                var content = '<li>'
                content += '<a href="/news/' + news.id + '" class="news_pic fl"><img src="' + news.index_image_url + '?imageView2/1/w/170/h/170"></a>'
                content += '<a href="/news/' + news.id + '" class="news_title fl">' + news.title + '</a>'
                content += '<a href="/news/' + news.id + '" class="news_detail fl">' + news.digest + '</a>'
                content += '<div class="author_info fl">'
                content += '<div class="source fl">来源：' + news.source + '</div>'
                content += '<div class="time fl">' + news.create_time + '</div>'
                content += '</div>'
                content += '</li>'
                $(".list_con").append(content)
            }
        }
        else {
            alert(response.errmsg)
        }
    })
}
//
// <li>
// <a href="#" class="news_pic fl"><img src="../../static/news/images/news_pic.jpg"></a>
// <a href="#" class="news_title fl">日本史上最大IPO之一要来了：软银计划将手机业务分拆上市软银计划将手机业务分拆上市</a>
// <a href="#" class="news_detail fl">据日经新闻网，软银计划让旗下核心业务移动手机部门SoftBank Corp.分拆上市，或募资2万亿日元(约180亿美元)。随着软银逐步向投资公司转型，此举旨在给手机业务部门更多自主权。</a>
// <div class="author_info fl">
// <div class="author fl">
// <img src="../../static/news/images/person.png" alt="author">
// <a href="#">乐鸣</a>
// </div>
// <div class="time fl">2017-01-01 00:00:00</div>
// </div>
// </li>