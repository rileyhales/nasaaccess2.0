from tethys_sdk.base import TethysAppBase, url_map_maker


class nasaaccess2(TethysAppBase):
    """
    Tethys app class for nasaaccess2.
    """

    name = 'nasaaccess'
    index = 'nasaaccess2:home'
    icon = 'nasaaccess2/images/nasaaccess.png'
    package = 'nasaaccess2'
    root_url = 'nasaaccess2'
    color = '#3e557a'
    description = 'Place a brief description of your app here.'
    tags = ''
    enable_feedback = False
    feedback_emails = []

    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)

        url_maps = (
            UrlMap(
                name='home',
                url='nasaaccess2',
                controller='nasaaccess2.controllers.home'
            ),
            UrlMap(
                name='download_files',
                url='nasaaccess2/run',
                controller='nasaaccess2.ajax_controllers.run_nasaaccess'
            ),
            UrlMap(
                name='upload_shapefiles',
                url='nasaaccess2/upload_shp',
                controller='nasaaccess2.ajax_controllers.upload_shapefiles'
            ),
            UrlMap(
                name='upload_tiffiles',
                url='nasaaccess2/upload_dem',
                controller='nasaaccess2.ajax_controllers.upload_tiffiles'
            ),
            UrlMap(
                name='download',
                url='nasaaccess2/download',
                controller='nasaaccess2.ajax_controllers.download_data'
            )
        )

        return url_maps
